"""Daily limit service for soft training limits."""

from datetime import date, datetime, timezone
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from .daily_limit import DailyTrainingSession


def check_daily_limit(db: DBSession, category: str) -> dict:
    """Check if daily limit is exceeded for a category.

    Returns:
        dict with keys:
            - exceeded: bool - whether the limit is exceeded (1+ sessions completed)
            - completed: int - number of completed sessions today
            - can_continue: bool - always True (soft limit)
    """
    today = date.today()

    completed_count = (
        db.query(func.count(DailyTrainingSession.id))
        .filter(DailyTrainingSession.category == category)
        .filter(DailyTrainingSession.training_date == today)
        .filter(DailyTrainingSession.completed_at.isnot(None))
        .scalar()
    ) or 0

    return {
        "exceeded": completed_count >= 1,
        "completed": completed_count,
        "can_continue": True,  # Soft limit - always allow continuing
    }


def get_all_categories_status(db: DBSession) -> dict:
    """Get daily training status for all categories.

    Returns:
        dict with keys 'words', 'phrasal', 'irregular', each containing:
            - completed: int - number of completed sessions today
            - exceeded: bool - whether the limit is exceeded
    """
    categories = ["words", "phrasal", "irregular"]
    result = {}

    for category in categories:
        status = check_daily_limit(db, category)
        result[category] = {
            "completed": status["completed"],
            "exceeded": status["exceeded"],
        }

    return result


def record_session_start(db: DBSession, category: str, session_id: int) -> DailyTrainingSession:
    """Record the start of a training session.

    Args:
        db: Database session
        category: Training category ('words', 'phrasal', 'irregular')
        session_id: ID of the training session

    Returns:
        Created DailyTrainingSession record
    """
    today = date.today()

    record = DailyTrainingSession(
        category=category,
        training_date=today,
        session_id=session_id,
        completed_at=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def record_session_complete(db: DBSession, session_id: int) -> DailyTrainingSession | None:
    """Record the completion of a training session.

    Args:
        db: Database session
        session_id: ID of the training session

    Returns:
        Updated DailyTrainingSession record or None if not found
    """
    record = (
        db.query(DailyTrainingSession)
        .filter(DailyTrainingSession.session_id == session_id)
        .first()
    )

    if record:
        record.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)

    return record
