"""Training service -- orchestrates session lifecycle and answer processing."""

import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql.expression import func

from backend.shared.date_utils import utc_now
from backend.shared.text_utils import normalize_text, levenshtein_distance, get_translations, get_first_translation, parse_json_field
from backend.shared.constants import CONSECUTIVE_CORRECT_TO_LEVEL_UP

from . import repository
from .exceptions import SessionAlreadyEndedError
from .schemas import (
    AnswerResult,
    AnswerSubmit,
    ExercisePhase,
    ExerciseResponse,
    SessionProgress,
    SessionResponse,
    SessionSummary,
    StartSessionResponse,
)


# ---------------------------------------------------------------------------
# Exercise generation
# ---------------------------------------------------------------------------

# Sequence of exercise types for new words (multiple exercises per word)
NEW_WORD_EXERCISE_SEQUENCE = [1, 2, 3, 4]  # Intro, Recognition, Recall, Context

# Exercise type names for phases
EXERCISE_TYPE_NAMES = {
    1: ("Introduction", "Знакомство"),
    2: ("Recognition", "Узнавание"),
    3: ("Recall", "Вспоминание"),
    4: ("Context", "Контекст"),
    5: ("Sentence Builder", "Составление предложений"),
    6: ("Free Production", "Свободное использование"),
    7: ("Listening", "Аудирование"),
}


def _generate_exercise(
    db: DBSession,
    word_id: int,
    mastery_level: int,
    force_type: int | None = None,
) -> ExerciseResponse:
    """Generate an exercise for a word based on its mastery level."""
    from backend.modules.words.models import Word, WordContext

    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise ValueError(f"Word {word_id} not found")

    # Get a context sentence if available
    context = (
        db.query(WordContext)
        .filter(WordContext.word_id == word_id)
        .first()
    )

    # Determine exercise type based on mastery level (1-7) or force_type
    exercise_type = force_type if force_type is not None else max(1, min(mastery_level, 7))

    # Parse JSON fields safely
    verb_forms = parse_json_field(word.verb_forms)
    collocations = parse_json_field(word.collocations)
    phrasal_verbs = parse_json_field(word.phrasal_verbs)
    usage_notes = parse_json_field(word.usage_notes)
    translations = get_translations(word)

    # Check if this is a function word and get rich context data
    is_function_word = word.word_category in ("function", "preposition")
    usage_rules = None
    comparisons = None
    common_errors = None

    if is_function_word:
        from .context_service import _get_function_word_data
        func_data = _get_function_word_data(db, word_id)
        usage_rules = func_data.get("usage_rules") or None
        comparisons = func_data.get("comparisons") or None
        common_errors = func_data.get("common_errors") or None

    # Base exercise data
    exercise = ExerciseResponse(
        word_id=word_id,
        exercise_type=exercise_type,
        english=word.english,
        transcription=word.transcription,
        translations=translations,
        part_of_speech=word.part_of_speech,
        sentence_en=context.sentence_en if context else None,
        sentence_ru=context.sentence_ru if context else None,
        verb_forms=verb_forms,
        collocations=collocations,
        phrasal_verbs=phrasal_verbs,
        usage_notes=usage_notes,
        is_function_word=is_function_word,
        usage_rules=usage_rules,
        comparisons=comparisons,
        common_errors=common_errors,
    )

    # Add options for recognition/context exercises (types 2, 4)
    if exercise_type in (2, 4):
        distractors = _get_distractors(db, word_id, word.part_of_speech, count=3)
        correct_answer = translations[0] if translations else word.english
        options = [correct_answer] + distractors
        random.shuffle(options)
        exercise.options = options

    # Add scrambled words for sentence builder (type 5)
    if exercise_type == 5 and context and context.sentence_en:
        words = context.sentence_en.replace(".", "").replace(",", "").split()
        random.shuffle(words)
        exercise.scrambled_words = words

    # Add hint for listening exercise (type 7)
    if exercise_type == 7:
        if word.english:
            hint = f"{word.english[0]}{'_' * (len(word.english) - 1)}"
            exercise.hint = hint

    # Sometimes reverse the exercise (show translation, guess english)
    if exercise_type == 2 and random.random() < 0.3:
        exercise.reverse = True
        # For reverse, options should be English words
        from backend.modules.words.models import Word
        other_words = (
            db.query(Word.english)
            .filter(Word.id != word_id)
            .order_by(func.random())
            .limit(3)
            .all()
        )
        exercise.options = [word.english] + [w[0] for w in other_words]
        random.shuffle(exercise.options)

    return exercise


def _generate_new_word_exercises(
    db: DBSession,
    word_id: int,
) -> list[ExerciseResponse]:
    """Generate multiple exercises for a new word (Intro, Recognition, Recall, Context)."""
    exercises = []
    for ex_type in NEW_WORD_EXERCISE_SEQUENCE:
        try:
            ex = _generate_exercise(db, word_id, mastery_level=1, force_type=ex_type)
            exercises.append(ex)
        except Exception:
            continue
    return exercises


def _get_distractors(
    db: DBSession,
    word_id: int,
    part_of_speech: str | None,
    count: int = 3,
) -> list[str]:
    """Get distractor translations for multiple choice exercises."""
    from backend.modules.words.models import Word
    from sqlalchemy.sql.expression import func

    query = db.query(Word).filter(Word.id != word_id)
    if part_of_speech:
        query = query.filter(Word.part_of_speech == part_of_speech)

    words = query.order_by(func.random()).limit(count).all()
    distractors = []
    for w in words:
        first_trans = get_first_translation(w)
        if first_trans:
            distractors.append(first_trans)
    return distractors


def refresh_session_contexts(
    db: DBSession, session_result: "StartSessionResponse"
) -> "StartSessionResponse":
    """Refresh exercise contexts after AI generation.

    Re-fetches context sentences for all exercises in the session.
    """
    from backend.modules.words.models import WordContext
    from .context_service import get_best_context

    for exercise in session_result.exercises:
        context = get_best_context(db, exercise.word_id)
        if context:
            exercise.sentence_en = context.sentence_en
            exercise.sentence_ru = context.sentence_ru

            # Update scrambled words for sentence builder
            if exercise.exercise_type == 5 and context.sentence_en:
                words = context.sentence_en.replace(".", "").replace(",", "").split()
                random.shuffle(words)
                exercise.scrambled_words = words

    return session_result


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def create_session(db: DBSession, duration_minutes: int | None = None) -> StartSessionResponse:
    """Start a new training session with exercises grouped by phases.

    Phase structure (per TRAINING-SPEC.md):
    1. Review words - grouped by mastery level (all level 2, then 3, then 4...)
    2. New words - grouped by exercise type (all Intro, then Recognition, then Recall, then Context)
    """
    from backend.modules.learning.models import UserWord
    from backend.modules.words.models import Word
    from backend.modules.settings.repository import get_settings
    from sqlalchemy.sql.expression import func
    from collections import defaultdict

    # Load user settings
    settings = get_settings(db)

    max_reviews = settings.max_reviews_per_session or 50
    daily_new = settings.daily_new_words or 10
    new_position = settings.new_words_position or "end"  # start/middle/end

    session = repository.create_session(db)

    # Get words for the session
    now = datetime.now(timezone.utc)

    # 1. Get overdue words (need review) - limited by max_reviews
    overdue_words = (
        db.query(UserWord)
        .filter(UserWord.next_review_at <= now)
        .order_by(UserWord.next_review_at.asc())
        .limit(max_reviews)
        .all()
    )

    # 2. Get words in learning/relearning state
    learning_word_ids = {uw.word_id for uw in overdue_words}
    learning_words = (
        db.query(UserWord)
        .filter(UserWord.fsrs_state.in_([1, 3]))
        .filter(UserWord.word_id.notin_(learning_word_ids))
        .limit(max_reviews // 2)
        .all()
    )

    # 3. Get new words (not yet in learning) - strictly limited by daily_new
    existing_ids = db.query(UserWord.word_id).subquery()
    new_words = (
        db.query(Word)
        .filter(Word.id.notin_(existing_ids))
        .order_by(Word.frequency_rank.asc().nullslast())
        .limit(daily_new)
        .all()
    )

    # --- Generate review exercises grouped by mastery level ---
    review_by_level: dict[int, list[ExerciseResponse]] = defaultdict(list)
    all_review_words = list(overdue_words) + list(learning_words)

    for uw in all_review_words:
        if sum(len(exs) for exs in review_by_level.values()) >= max_reviews:
            break
        try:
            ex = _generate_exercise(db, uw.word_id, uw.mastery_level)
            review_by_level[uw.mastery_level].append(ex)
        except Exception:
            continue

    # --- Generate new word exercises grouped by exercise type ---
    new_by_type: dict[int, list[ExerciseResponse]] = defaultdict(list)

    for word in new_words:
        for ex_type in NEW_WORD_EXERCISE_SEQUENCE:
            try:
                ex = _generate_exercise(db, word.id, mastery_level=1, force_type=ex_type)
                new_by_type[ex_type].append(ex)
            except Exception:
                continue

    # --- Build phases ---
    phases: list[ExercisePhase] = []

    # Review phases (sorted by level)
    for level in sorted(review_by_level.keys()):
        exercises = review_by_level[level]
        if exercises:
            name_en, name_ru = EXERCISE_TYPE_NAMES.get(level, (f"Level {level}", f"Уровень {level}"))
            phases.append(ExercisePhase(
                phase_type="review",
                exercise_type=level,
                name=name_en,
                name_ru=name_ru,
                exercises=exercises,
                count=len(exercises),
            ))

    # New word phases (in sequence order: 1, 2, 3, 4)
    for ex_type in NEW_WORD_EXERCISE_SEQUENCE:
        exercises = new_by_type.get(ex_type, [])
        if exercises:
            name_en, name_ru = EXERCISE_TYPE_NAMES.get(ex_type, (f"Type {ex_type}", f"Тип {ex_type}"))
            phases.append(ExercisePhase(
                phase_type="new",
                exercise_type=ex_type,
                name=name_en,
                name_ru=name_ru,
                exercises=exercises,
                count=len(exercises),
            ))

    # --- Build flat exercise list for backwards compatibility ---
    flat_exercises: list[ExerciseResponse] = []

    # Collect review and new exercises
    review_flat = [ex for level in sorted(review_by_level.keys()) for ex in review_by_level[level]]
    new_flat = [ex for ex_type in NEW_WORD_EXERCISE_SEQUENCE for ex in new_by_type.get(ex_type, [])]

    # Combine based on new_words_position setting
    if new_position == "start":
        flat_exercises = new_flat + review_flat
    elif new_position == "middle":
        mid = len(review_flat) // 2
        flat_exercises = review_flat[:mid] + new_flat + review_flat[mid:]
    else:  # "end"
        flat_exercises = review_flat + new_flat

    words_reviewed = len(review_flat)
    words_new = len(new_words)

    # Update session with word counts
    repository.update_session(db, session.id, {
        "words_reviewed": words_reviewed,
        "words_new": words_new,
    })

    # --- Track new words for deferred UserWord creation ---
    from .models import SessionNewWordProgress

    for word in new_words:
        progress = SessionNewWordProgress(
            session_id=session.id,
            word_id=word.id,
        )
        db.add(progress)
    db.commit()

    return StartSessionResponse(
        session_id=session.id,
        exercises=flat_exercises,
        phases=phases,
        total_words=len(flat_exercises),
        total_exercises=len(flat_exercises),
        review_words_count=words_reviewed,
        new_words_count=words_new,
    )


def get_session(db: DBSession, session_id: int) -> SessionResponse:
    """Return a single session by its id."""
    session = repository.get_session(db, session_id)
    return SessionResponse.model_validate(session)


def get_progress(db: DBSession, session_id: int) -> SessionProgress:
    """Return live progress counters for an active session."""
    session = repository.get_session(db, session_id)
    wrong = session.total_count - session.correct_count
    return SessionProgress(
        current_index=session.total_count,
        total_words=session.words_reviewed + session.words_new,
        correct=session.correct_count,
        wrong=wrong,
    )


# ---------------------------------------------------------------------------
# Answer processing
# ---------------------------------------------------------------------------

def _evaluate_answer(submitted: str, correct: str) -> tuple[bool, int]:
    """Compare a submitted answer to the expected one.

    Returns (is_correct, rating) where rating is 0-5:
        5 -- exact match
        4 -- match ignoring case / whitespace
        3 -- within Levenshtein distance 1 (typo tolerance)
        0 -- wrong
    """
    norm_submitted = normalize_text(submitted)
    norm_correct = normalize_text(correct)

    if norm_submitted == norm_correct:
        return True, 5

    distance = levenshtein_distance(norm_submitted, norm_correct)
    if distance <= 1 and len(norm_correct) > 3:
        return True, 3

    return False, 0


def record_answer(
    db: DBSession,
    session_id: int,
    answer: AnswerSubmit,
) -> AnswerResult:
    """Evaluate a learner's answer and update progress.

    For NEW words: Only track results in SessionNewWordProgress.
                   UserWord will be created at session end if >= 3/4 correct.
    For REVIEW words: Update UserWord and FSRS as before.
    """
    from backend.modules.words.models import Word
    from backend.modules.learning.service import LearningService
    from backend.modules.learning.schemas import ReviewCreate
    from backend.modules.learning.repository import LearningRepository
    from .models import SessionNewWordProgress

    session = repository.get_session(db, session_id)
    if session.ended_at is not None:
        raise SessionAlreadyEndedError(session_id)

    # Fetch the word
    word = db.query(Word).filter(Word.id == answer.word_id).first()
    correct_answer = get_first_translation(word) if word else ""

    # Evaluate answer
    if answer.exercise_type == 1:
        # Introduction - always correct, user acknowledges seeing word
        is_correct = True
        fsrs_rating = 4  # Easy - just saw the word
    else:
        is_correct, score = _evaluate_answer(answer.answer, correct_answer)
        # Map score to FSRS rating: 1=Again, 2=Hard, 3=Good, 4=Easy
        if not is_correct:
            fsrs_rating = 1  # Again
        elif score >= 5:
            fsrs_rating = 4  # Easy - exact match
        elif score >= 3:
            fsrs_rating = 3  # Good - minor typo
        else:
            fsrs_rating = 2  # Hard

    # Update session counters
    update_data: dict = {"total_count": session.total_count + 1}
    if is_correct:
        update_data["correct_count"] = session.correct_count + 1
    repository.update_session(db, session_id, update_data)

    # Check if this is a NEW word in this session
    new_word_progress = (
        db.query(SessionNewWordProgress)
        .filter(SessionNewWordProgress.session_id == session_id)
        .filter(SessionNewWordProgress.word_id == answer.word_id)
        .first()
    )

    if new_word_progress:
        # --- NEW WORD: Track result, DON'T create UserWord yet ---
        # Update the appropriate exercise result
        if answer.exercise_type == 1:
            new_word_progress.exercise_1_correct = is_correct
        elif answer.exercise_type == 2:
            new_word_progress.exercise_2_correct = is_correct
        elif answer.exercise_type == 3:
            new_word_progress.exercise_3_correct = is_correct
        elif answer.exercise_type == 4:
            new_word_progress.exercise_4_correct = is_correct
        db.commit()

        # Return result without mastery tracking (word not learned yet)
        feedback = None
        if not is_correct:
            feedback = f"Правильный ответ: {correct_answer}"

        return AnswerResult(
            correct=is_correct,
            rating=fsrs_rating,
            correct_answer=correct_answer,
            feedback=feedback,
            mastery_level=1,  # Not learned yet
            level_changed=False,
        )

    # --- REVIEW WORD: Update UserWord and FSRS as normal ---
    learning_service = LearningService()
    learning_repo = LearningRepository()

    user_word = learning_repo.get_user_word(db, answer.word_id)
    if not user_word:
        # Edge case: word should exist but doesn't, initialize it
        user_word = learning_service.initialize_word(db, answer.word_id)

    # Record the review to update mastery and FSRS
    review = ReviewCreate(
        exercise_type=answer.exercise_type,
        rating=fsrs_rating,
        response_time_ms=answer.response_time_ms,
        correct=is_correct,
    )
    mastery_result = learning_service.record_review(db, answer.word_id, review)

    feedback = None
    if not is_correct:
        feedback = f"Правильный ответ: {correct_answer}"

    return AnswerResult(
        correct=is_correct,
        rating=fsrs_rating,
        correct_answer=correct_answer,
        feedback=feedback,
        mastery_level=mastery_result.new_level,
        level_changed=mastery_result.level_changed,
    )


# ---------------------------------------------------------------------------
# End session
# ---------------------------------------------------------------------------

def end_session(db: DBSession, session_id: int) -> SessionSummary:
    """Finalize a training session and return a summary.

    For new words: Creates UserWord only if >= 3/4 exercises were correct.
    Words with < 3 correct will appear as new again in future sessions.
    """
    from backend.modules.learning.service import LearningService
    from .models import SessionNewWordProgress

    session = repository.get_session(db, session_id)
    if session.ended_at is not None:
        raise SessionAlreadyEndedError(session_id)

    # --- Finalize new words ---
    new_word_progress_list = (
        db.query(SessionNewWordProgress)
        .filter(SessionNewWordProgress.session_id == session_id)
        .all()
    )

    learning_service = LearningService()
    new_words_learned = 0
    level_ups = 0

    for progress in new_word_progress_list:
        correct_count = progress.get_correct_count()

        # TRAINING-SPEC.md: Only create UserWord if >= 3 out of 4 correct
        if correct_count >= 3:
            try:
                # Create UserWord starting at mastery level 2 (skip Introduction)
                learning_service.initialize_word(db, progress.word_id, initial_mastery=2)
                progress.learned = True
                new_words_learned += 1
            except Exception:
                # Word might already exist from a previous session - that's OK
                progress.learned = True
        else:
            # Word not learned - will appear as new again in future
            progress.learned = False

    db.commit()

    # End the session
    session = repository.end_session(db, session_id)

    wrong = session.total_count - session.correct_count
    accuracy = (
        round(session.correct_count / session.total_count * 100, 1)
        if session.total_count > 0
        else 0.0
    )

    return SessionSummary(
        total_words=session.total_count,
        correct=session.correct_count,
        wrong=wrong,
        accuracy=accuracy,
        new_words_learned=new_words_learned,  # Actual learned count, not attempted
        time_spent_seconds=session.duration_seconds,
        level_ups=level_ups,
    )
