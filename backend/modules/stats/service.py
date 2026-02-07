from datetime import date, timedelta
import logging
from sqlalchemy.orm import Session

from backend.shared.date_utils import today
from backend.shared.constants import COVERAGE_THRESHOLDS
from .schemas import DashboardResponse, DailyStatsResponse, CoverageResponse, HeatmapData
from .repository import get_or_create_today, get_daily_stats_range, get_streak as repo_get_streak, update_daily_stats

logger = logging.getLogger(__name__)


def get_dashboard(db: Session) -> DashboardResponse:
    """Build the full dashboard response."""
    today_stats = get_or_create_today(db)
    streak = repo_get_streak(db)

    # Weekly data: last 7 days
    end = today()
    start = end - timedelta(days=6)
    weekly_rows = get_daily_stats_range(db, start, end)
    weekly_lookup = {str(row.date): row for row in weekly_rows}

    weekly_data = []
    for i in range(7):
        d = start + timedelta(days=i)
        ds = str(d)
        if ds in weekly_lookup:
            row = weekly_lookup[ds]
            weekly_data.append({
                "date": ds,
                "words_reviewed": row.words_reviewed,
                "words_learned": row.words_learned,
                "accuracy": row.accuracy,
            })
        else:
            weekly_data.append({
                "date": ds,
                "words_reviewed": 0,
                "words_learned": 0,
                "accuracy": 0,
            })

    # Level distribution from the learning module
    from backend.modules.learning.repository import LearningRepository
    level_distribution = LearningRepository.count_by_level(db)
    total_words_known = sum(
        count for level, count in level_distribution.items() if level >= 1
    )
    coverage_percent = calculate_coverage(total_words_known)

    return DashboardResponse(
        streak=streak,
        today_reviewed=today_stats.words_reviewed,
        today_learned=today_stats.words_learned,
        today_accuracy=today_stats.accuracy,
        weekly_data=weekly_data,
        level_distribution=level_distribution,
        coverage_percent=coverage_percent,
        total_words_known=total_words_known,
    )


def record_review(db: Session, correct: bool) -> None:
    """Record a single review event."""
    update_daily_stats(db, words_reviewed_delta=1, correct=correct)


def get_daily_stats(db: Session, from_date: date, to_date: date) -> list[DailyStatsResponse]:
    """Get daily stats for a date range."""
    rows = get_daily_stats_range(db, from_date, to_date)
    return [
        DailyStatsResponse(
            date=str(row.date),
            words_reviewed=row.words_reviewed,
            words_learned=row.words_learned,
            time_spent=row.time_spent,
            accuracy=row.accuracy,
            streak=row.streak,
        )
        for row in rows
    ]


def calculate_coverage(known_words_count: int) -> float:
    """
    Calculate estimated text coverage percentage based on known word count.
    Uses linear interpolation between COVERAGE_THRESHOLDS breakpoints.
    """
    if known_words_count <= 0:
        return 0.0

    thresholds = COVERAGE_THRESHOLDS

    # Below the first threshold: interpolate from (0, 0)
    if known_words_count <= thresholds[0][0]:
        words_t, cov_t = thresholds[0]
        return round(known_words_count / words_t * cov_t, 2)

    # Between thresholds: linear interpolation
    for i in range(1, len(thresholds)):
        words_prev, cov_prev = thresholds[i - 1]
        words_curr, cov_curr = thresholds[i]
        if known_words_count <= words_curr:
            ratio = (known_words_count - words_prev) / (words_curr - words_prev)
            return round(cov_prev + ratio * (cov_curr - cov_prev), 2)

    # Above the last threshold
    return thresholds[-1][1]


def get_heatmap(db: Session, year: int) -> list[HeatmapData]:
    """Generate GitHub-style heatmap data for a given year."""
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    rows = get_daily_stats_range(db, start, end)
    lookup = {str(row.date): row.words_reviewed for row in rows}

    # Determine max for level calculation
    max_count = max((r.words_reviewed for r in rows), default=1) or 1

    heatmap: list[HeatmapData] = []
    current = start
    while current <= end:
        ds = str(current)
        count = lookup.get(ds, 0)
        if count == 0:
            level = 0
        elif count <= max_count * 0.25:
            level = 1
        elif count <= max_count * 0.5:
            level = 2
        elif count <= max_count * 0.75:
            level = 3
        else:
            level = 4
        heatmap.append(HeatmapData(date=ds, count=count, level=level))
        current += timedelta(days=1)

    return heatmap


def get_streak(db: Session) -> int:
    """Get the current streak count."""
    return repo_get_streak(db)
