from datetime import datetime

from pydantic import BaseModel, Field, computed_field


# ---------------------------------------------------------------------------
# Session DTOs
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    duration_minutes: int = Field(default=15, ge=1, le=120)


class SessionResponse(BaseModel):
    id: int
    started_at: datetime
    ended_at: datetime | None = None
    words_reviewed: int = 0
    words_new: int = 0
    correct_count: int = 0
    total_count: int = 0
    duration_seconds: int = 0

    @computed_field
    @property
    def accuracy(self) -> float:
        if self.total_count == 0:
            return 0.0
        return round(self.correct_count / self.total_count * 100, 1)

    model_config = {"from_attributes": True}


class StartSessionResponse(BaseModel):
    """Response for starting a new session with generated exercises."""
    session_id: int
    exercises: list["ExerciseResponse"]
    total_words: int


class SessionProgress(BaseModel):
    current_index: int
    total_words: int
    correct: int
    wrong: int


# ---------------------------------------------------------------------------
# Exercise DTOs
# ---------------------------------------------------------------------------

class ExerciseResponse(BaseModel):
    word_id: int
    exercise_type: int = Field(..., ge=1, le=7)
    english: str
    transcription: str | None = None
    translations: list[str] = []
    part_of_speech: str | None = None
    options: list[str] | None = None
    sentence_en: str | None = None
    sentence_ru: str | None = None
    scrambled_words: list[str] | None = None
    hint: str | None = None
    reverse: bool = False


# ---------------------------------------------------------------------------
# Answer DTOs
# ---------------------------------------------------------------------------

class AnswerSubmit(BaseModel):
    word_id: int
    answer: str
    response_time_ms: int = Field(..., ge=0)


class AnswerResult(BaseModel):
    correct: bool
    rating: int = Field(..., ge=0, le=5)
    correct_answer: str
    feedback: str | None = None
    mastery_level: int
    level_changed: bool


# ---------------------------------------------------------------------------
# Summary DTO
# ---------------------------------------------------------------------------

class SessionSummary(BaseModel):
    total_words: int
    correct: int
    wrong: int
    accuracy: float
    new_words_learned: int
    time_spent_seconds: int
    level_ups: int


# Rebuild models to resolve forward references
StartSessionResponse.model_rebuild()
