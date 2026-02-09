"""Training service -- orchestrates session lifecycle and answer processing."""

import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql.expression import func

from backend.shared.date_utils import utc_now
from backend.shared.text_utils import normalize_text, levenshtein_distance
from backend.shared.constants import CONSECUTIVE_CORRECT_TO_LEVEL_UP

from . import repository
from .exceptions import SessionAlreadyEndedError
from .schemas import (
    AnswerResult,
    AnswerSubmit,
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

    # Parse JSON fields if present
    import json

    verb_forms = None
    collocations = None
    phrasal_verbs = None
    usage_notes = None

    if word.verb_forms:
        try:
            verb_forms = json.loads(word.verb_forms) if isinstance(word.verb_forms, str) else word.verb_forms
        except:
            pass
    if word.collocations:
        try:
            collocations = json.loads(word.collocations) if isinstance(word.collocations, str) else word.collocations
        except:
            pass
    if word.phrasal_verbs:
        try:
            phrasal_verbs = json.loads(word.phrasal_verbs) if isinstance(word.phrasal_verbs, str) else word.phrasal_verbs
        except:
            pass
    if word.usage_notes:
        try:
            usage_notes = json.loads(word.usage_notes) if isinstance(word.usage_notes, str) else word.usage_notes
        except:
            pass

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
        translations=word.translations or [],
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
        correct_answer = word.translations[0] if word.translations else word.english
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
        if w.translations:
            distractors.append(w.translations[0])
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
    """Start a new training session with generated exercises."""
    from backend.modules.learning.models import UserWord
    from backend.modules.words.models import Word
    from backend.modules.settings.repository import get_settings
    from sqlalchemy.sql.expression import func

    # Load user settings
    settings = get_settings(db)

    # Use settings values (with fallbacks)
    duration = duration_minutes or settings.session_duration_minutes or 15
    max_reviews = settings.max_reviews_per_session or 50
    daily_new = settings.daily_new_words or 10
    new_position = settings.new_words_position or "end"  # start/middle/end

    session = repository.create_session(db)

    # Get words for the session
    now = datetime.now(timezone.utc)
    review_exercises: list[ExerciseResponse] = []
    new_exercises: list[ExerciseResponse] = []

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
        .limit(daily_new)  # Strict limit on new words
        .all()
    )

    # Generate review exercises
    for uw in overdue_words:
        if len(review_exercises) >= max_reviews:
            break
        try:
            ex = _generate_exercise(db, uw.word_id, uw.mastery_level)
            review_exercises.append(ex)
        except Exception:
            continue

    for uw in learning_words:
        if len(review_exercises) >= max_reviews:
            break
        try:
            ex = _generate_exercise(db, uw.word_id, uw.mastery_level)
            review_exercises.append(ex)
        except Exception:
            continue

    # Generate new word exercises (multiple exercises per new word)
    for word in new_words:
        word_exercises = _generate_new_word_exercises(db, word.id)
        new_exercises.extend(word_exercises)

    # Combine based on new_words_position setting
    exercises: list[ExerciseResponse] = []
    if new_position == "start":
        exercises = new_exercises + review_exercises
    elif new_position == "middle":
        mid = len(review_exercises) // 2
        exercises = review_exercises[:mid] + new_exercises + review_exercises[mid:]
    else:  # "end"
        exercises = review_exercises + new_exercises

    words_reviewed = len(review_exercises)
    words_new = len(new_words)  # Count unique new words, not exercises

    # Update session with word counts
    repository.update_session(db, session.id, {
        "words_reviewed": words_reviewed,
        "words_new": words_new,
    })

    return StartSessionResponse(
        session_id=session.id,
        exercises=exercises,
        total_words=len(exercises),
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
    """Evaluate a learner's answer and update mastery level via FSRS."""
    from backend.modules.words.models import Word
    from backend.modules.learning.service import LearningService
    from backend.modules.learning.schemas import ReviewCreate
    from backend.modules.learning.repository import LearningRepository

    session = repository.get_session(db, session_id)
    if session.ended_at is not None:
        raise SessionAlreadyEndedError(session_id)

    # Fetch the word
    word = db.query(Word).filter(Word.id == answer.word_id).first()
    correct_answer = word.translations[0] if word and word.translations else ""

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

    # Initialize or update the word in learning system
    learning_service = LearningService()
    learning_repo = LearningRepository()

    user_word = learning_repo.get_user_word(db, answer.word_id)
    if not user_word:
        # First time seeing this word - initialize it
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
    """Finalize a training session and return a summary."""
    session = repository.get_session(db, session_id)
    if session.ended_at is not None:
        raise SessionAlreadyEndedError(session_id)

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
        new_words_learned=session.words_new,
        time_spent_seconds=session.duration_seconds,
        level_ups=0,
    )
