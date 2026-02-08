from datetime import datetime
from pydantic import BaseModel, Field


class UserWordResponse(BaseModel):
    id: int
    word_id: int
    mastery_level: int
    consecutive_correct: int
    consecutive_wrong: int
    fsrs_stability: float
    fsrs_difficulty: float
    fsrs_state: int
    fsrs_reps: int
    fsrs_lapses: int
    next_review_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserWordWithWord(UserWordResponse):
    english: str = ""
    transcription: str | None = None
    translations: list[str] = []
    part_of_speech: str | None = None


class ReviewCreate(BaseModel):
    exercise_type: int
    rating: int = Field(..., ge=1, le=4)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    response_time_ms: int = Field(..., ge=0)
    correct: bool


class ReviewResponse(BaseModel):
    id: int
    user_word_id: int
    exercise_type: int
    rating: int
    response_time_ms: int
    correct: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MasteryResult(BaseModel):
    new_level: int
    level_changed: bool
    next_review: datetime | None = None


class LearningStatsResponse(BaseModel):
    total_words: int
    by_level: dict[int, int]
    by_state: dict[str, int]


class DueWordsResponse(BaseModel):
    overdue: list[UserWordWithWord]
    learning: list[UserWordWithWord]
    new_available: int


class PaginatedUserWords(BaseModel):
    items: list[UserWordResponse]
    total: int
    page: int
    per_page: int


# Phrasal Verb schemas
class UserPhrasalVerbResponse(BaseModel):
    id: int
    phrasal_verb_id: int
    mastery_level: int
    consecutive_correct: int
    consecutive_wrong: int
    fsrs_stability: float
    fsrs_difficulty: float
    fsrs_state: int
    fsrs_reps: int
    fsrs_lapses: int
    next_review_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserPhrasalVerbWithPhrasal(UserPhrasalVerbResponse):
    phrase: str = ""
    base_verb: str = ""
    particle: str = ""
    translations: list[str] = []
    definitions: list[dict] = []
    is_separable: bool = True


class PhrasalVerbReviewCreate(BaseModel):
    exercise_type: int
    rating: int = Field(..., ge=1, le=4)
    response_time_ms: int = Field(..., ge=0)
    correct: bool


class DuePhrasalVerbsResponse(BaseModel):
    overdue: list[UserPhrasalVerbWithPhrasal]
    learning: list[UserPhrasalVerbWithPhrasal]
    new_available: int


class PaginatedUserPhrasalVerbs(BaseModel):
    items: list[UserPhrasalVerbResponse]
    total: int
    page: int
    per_page: int


# Irregular Verb schemas
class UserIrregularVerbResponse(BaseModel):
    id: int
    irregular_verb_id: int
    mastery_level: int
    consecutive_correct: int
    consecutive_wrong: int
    fsrs_stability: float
    fsrs_difficulty: float
    fsrs_state: int
    fsrs_reps: int
    fsrs_lapses: int
    next_review_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserIrregularVerbWithIrregular(UserIrregularVerbResponse):
    base_form: str = ""
    past_simple: str = ""
    past_participle: str = ""
    translations: list[str] = []
    verb_pattern: str = ""
    transcription_base: str | None = None
    transcription_past: str | None = None
    transcription_participle: str | None = None


class IrregularVerbReviewCreate(BaseModel):
    exercise_type: int
    rating: int = Field(..., ge=1, le=4)
    response_time_ms: int = Field(..., ge=0)
    correct: bool


class DueIrregularVerbsResponse(BaseModel):
    overdue: list[UserIrregularVerbWithIrregular]
    learning: list[UserIrregularVerbWithIrregular]
    new_available: int


class PaginatedUserIrregularVerbs(BaseModel):
    items: list[UserIrregularVerbResponse]
    total: int
    page: int
    per_page: int


# Combined learning stats response
class CombinedLearningStatsResponse(BaseModel):
    words: LearningStatsResponse
    phrasal_verbs: dict
    irregular_verbs: dict
