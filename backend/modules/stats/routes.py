from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from .schemas import DashboardResponse, DailyStatsResponse, CoverageResponse, HeatmapData
from . import service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)):
    return service.get_dashboard(db)


@router.get("/daily", response_model=list[DailyStatsResponse])
def daily_stats(
    from_date: date = Query(alias="from", default=None),
    to_date: date = Query(alias="to", default=None),
    db: Session = Depends(get_db),
):
    if from_date is None:
        from_date = date.today() - timedelta(days=30)
    if to_date is None:
        to_date = date.today()
    return service.get_daily_stats(db, from_date, to_date)


@router.get("/coverage", response_model=CoverageResponse)
def coverage(db: Session = Depends(get_db)):
    from backend.modules.learning.repository import LearningRepository
    from backend.shared.constants import COVERAGE_THRESHOLDS

    level_counts = LearningRepository.count_by_level(db)
    known_words = sum(c for lv, c in level_counts.items() if lv >= 1)
    coverage_pct = service.calculate_coverage(known_words)

    next_milestone = {}
    for words_needed, cov in COVERAGE_THRESHOLDS:
        if known_words < words_needed:
            next_milestone = {
                "words_needed": words_needed,
                "coverage_at_milestone": cov,
                "words_remaining": words_needed - known_words,
            }
            break

    return CoverageResponse(
        known_words=known_words,
        coverage_percent=coverage_pct,
        next_milestone=next_milestone,
    )


@router.get("/heatmap", response_model=list[HeatmapData])
def heatmap(
    year: int = Query(default=None),
    db: Session = Depends(get_db),
):
    if year is None:
        year = date.today().year
    return service.get_heatmap(db, year)
