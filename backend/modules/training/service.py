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

def _generate_exercise(
    db: DBSession,
    word_id: int,
    mastery_level: int,
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

    # Determine exercise type based on mastery level (1-7)
    exercise_type = max(1, min(mastery_level, 7))

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

    session = repository.create_session(db)

    # Calculate target exercise count based on settings
    target_exercises = min(max_reviews, max(10, duration * 4))  # ~15 sec per exercise
    target_new_words = min(daily_new, target_exercises // 3)

    # Get words for the session
    now = datetime.now(timezone.utc)
    exercises: list[ExerciseResponse] = []

    # 1. Get overdue words (need review)
    overdue_words = (
        db.query(UserWord)
        .filter(UserWord.next_review_at <= now)
        .order_by(UserWord.next_review_at.asc())
        .limit(target_exercises)
        .all()
    )

    # 2. Get words in learning/relearning state
    learning_words = (
        db.query(UserWord)
        .filter(UserWord.fsrs_state.in_([1, 3]))
        .limit(target_exercises // 2)
        .all()
    )

    # 3. Get new words (not yet in learning) - from most frequent
    existing_ids = db.query(UserWord.word_id).subquery()
    new_words = (
        db.query(Word)
        .filter(Word.id.notin_(existing_ids))
        .order_by(Word.frequency_rank.asc().nullslast())
        .limit(target_new_words)
        .all()
    )

    # Combine and generate exercises
    words_reviewed = 0
    words_new = 0

    # Add overdue exercises
    for uw in overdue_words:
        if len(exercises) >= target_exercises:
            break
        try:
            ex = _generate_exercise(db, uw.word_id, uw.mastery_level)
            exercises.append(ex)
            words_reviewed += 1
        except Exception:
            continue

    # Add learning exercises
    for uw in learning_words:
        if len(exercises) >= target_exercises:
            break
        if uw.word_id not in [e.word_id for e in exercises]:
            try:
                ex = _generate_exercise(db, uw.word_id, uw.mastery_level)
                exercises.append(ex)
                words_reviewed += 1
            except Exception:
                continue

    # Add new words (level 1 - introduction)
    for word in new_words:
        if len(exercises) >= target_exercises:
            break
        try:
            ex = _generate_exercise(db, word.id, 1)
            exercises.append(ex)
            words_new += 1
        except Exception:
            continue

    # If still not enough exercises, get more words from dictionary
    if len(exercises) < target_exercises:
        remaining = target_exercises - len(exercises)
        used_word_ids = {e.word_id for e in exercises}
        more_words = (
            db.query(Word)
            .filter(Word.id.notin_(used_word_ids))
            .order_by(Word.frequency_rank.asc().nullslast())
            .limit(remaining)
            .all()
        )
        for word in more_words:
            try:
                ex = _generate_exercise(db, word.id, 1)
                exercises.append(ex)
                words_new += 1
            except Exception:
                continue

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
    """Evaluate a learner's answer and update the session counters.

    The correct answer is determined from the word record. Mastery-level
    promotion logic is simplified here; the learning module can hook into
    events for full SRS processing.
    """
    session = repository.get_session(db, session_id)
    if session.ended_at is not None:
        raise SessionAlreadyEndedError(session_id)

    # Fetch the word to obtain the expected answer
    from backend.modules.words.models import Word

    word = db.query(Word).filter(Word.id == answer.word_id).first()
    correct_answer = word.translations[0] if word and word.translations else ""

    # Level 1 (Introduction) is always correct - user just acknowledges seeing the word
    if answer.exercise_type == 1:
        is_correct = True
        rating = 4  # Good rating for introduction
    else:
        is_correct, rating = _evaluate_answer(answer.answer, correct_answer)

    # Update session counters
    update_data: dict = {"total_count": session.total_count + 1}
    if is_correct:
        update_data["correct_count"] = session.correct_count + 1
    repository.update_session(db, session_id, update_data)

    # Placeholder mastery tracking -- real SRS lives in the learning module
    mastery_level = 1
    level_changed = False

    feedback = None
    if not is_correct:
        feedback = f"The correct answer is: {correct_answer}"

    return AnswerResult(
        correct=is_correct,
        rating=rating,
        correct_answer=correct_answer,
        feedback=feedback,
        mastery_level=mastery_level,
        level_changed=level_changed,
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
