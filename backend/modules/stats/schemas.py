from pydantic import BaseModel


class DailyStatsResponse(BaseModel):
    date: str
    words_reviewed: int
    words_learned: int
    time_spent: int
    accuracy: float
    streak: int

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    streak: int
    today_reviewed: int
    today_learned: int
    today_accuracy: float
    weekly_data: list
    level_distribution: dict
    coverage_percent: float
    total_words_known: int


class CoverageResponse(BaseModel):
    known_words: int
    coverage_percent: float
    next_milestone: dict


class HeatmapData(BaseModel):
    date: str
    count: int
    level: int
