"""Training service -- orchestrates session lifecycle and answer processing."""

from sqlalchemy.orm import Session

from backend.shared.date_utils import utc_now
from backend.shared.text_utils import normalize_text, levenshtein_distance
from backend.shared.constants import CONSECUTIVE_CORRECT_TO_LEVEL_UP

from . import repository
from .exceptions import SessionAlreadyEndedError
from .schemas import (
    AnswerResult,
    AnswerSubmit,
    SessionProgress,
    SessionResponse,
    SessionSummary,
)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def create_session(db: Session) -> SessionResponse:
    """Start a new training session."""
    session = repository.create_session(db)
    return SessionResponse.model_validate(session)


def get_session(db: Session, session_id: int) -> SessionResponse:
    """Return a single session by its id."""
    session = repository.get_session(db, session_id)
    return SessionResponse.model_validate(session)


def get_progress(db: Session, session_id: int) -> SessionProgress:
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
    db: Session,
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

def end_session(db: Session, session_id: int) -> SessionSummary:
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
