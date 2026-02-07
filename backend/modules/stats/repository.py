from datetime import date, timedelta
from sqlalchemy.orm import Session

from backend.shared.date_utils import today
from .models import DailyStats


def get_or_create_today(db: Session) -> DailyStats:
    """Get today's stats row, creating it if it doesn't exist."""
    current_date = today()
    stats = db.query(DailyStats).filter(DailyStats.date == current_date).first()
    if not stats:
        stats = DailyStats(date=current_date)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def get_daily_stats_range(db: Session, from_date: date, to_date: date) -> list[DailyStats]:
    """Get daily stats within a date range (inclusive)."""
    return (
        db.query(DailyStats)
        .filter(DailyStats.date >= from_date, DailyStats.date <= to_date)
        .order_by(DailyStats.date)
        .all()
    )


def get_streak(db: Session) -> int:
    """Calculate the current consecutive-day streak."""
    current_date = today()
    streak = 0

    while True:
        check_date = current_date - timedelta(days=streak)
        stats = db.query(DailyStats).filter(DailyStats.date == check_date).first()
        if stats and stats.words_reviewed > 0:
            streak += 1
        else:
            break

    return streak


def update_daily_stats(
    db: Session,
    words_reviewed_delta: int = 0,
    words_learned_delta: int = 0,
    time_spent_delta: int = 0,
    correct: bool | None = None,
) -> DailyStats:
    """Update today's stats with incremental changes."""
    stats = get_or_create_today(db)

    stats.words_reviewed += words_reviewed_delta
    stats.words_learned += words_learned_delta
    stats.time_spent += time_spent_delta

    if correct is not None and stats.words_reviewed > 0:
        total_reviews = stats.words_reviewed
        previous_correct = round(stats.accuracy * (total_reviews - 1))
        new_correct = previous_correct + (1 if correct else 0)
        stats.accuracy = round(new_correct / total_reviews, 4)

    stats.streak = get_streak(db)

    db.commit()
    db.refresh(stats)
    return stats
