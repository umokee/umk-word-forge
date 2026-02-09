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


class ExercisePhase(BaseModel):
    """A phase of exercises grouped by type."""
    phase_type: str  # "review" or "new"
    exercise_type: int  # 1-7
    name: str  # "Знакомство", "Recognition", "Recall", "Context"
    name_ru: str  # Russian name for display
    exercises: list["ExerciseResponse"]
    count: int


class StartSessionResponse(BaseModel):
    """Response for starting a new session with generated exercises."""
    session_id: int
    exercises: list["ExerciseResponse"]  # Flat list for backwards compat
    phases: list[ExercisePhase] = []  # New: grouped by phases
    total_words: int
    total_exercises: int = 0
    review_words_count: int = 0
    new_words_count: int = 0
    daily_limit_warning: bool = False  # True if already trained today (soft limit)


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

    # Linguistic enrichment data
    verb_forms: dict | None = None
    collocations: list[dict] | None = None
    phrasal_verbs: list[dict] | None = None
    usage_notes: list[str] | None = None

    # Rich context for function words
    is_function_word: bool = False
    usage_rules: list[dict] | None = None  # [{"rule": "...", "example": "..."}]
    comparisons: list[dict] | None = None  # [{"vs": "a/an", "difference": "..."}]
    common_errors: list[dict] | None = None  # [{"wrong": "...", "correct": "...", "why": "..."}]


# ---------------------------------------------------------------------------
# Answer DTOs
# ---------------------------------------------------------------------------

class AnswerSubmit(BaseModel):
    word_id: int
    answer: str
    response_time_ms: int = Field(..., ge=0)
    exercise_type: int = Field(default=2, ge=1, le=7)  # 1-7, default to Recognition


class AnswerResult(BaseModel):
    correct: bool
    rating: int = Field(..., ge=0, le=5)
    correct_answer: str
    feedback: str | None = None
    mastery_level: int
    level_changed: bool


# ---------------------------------------------------------------------------
# Daily Status DTOs
# ---------------------------------------------------------------------------

class CategoryDailyStatus(BaseModel):
    completed: int
    exceeded: bool


class DailyStatusResponse(BaseModel):
    words: CategoryDailyStatus
    phrasal: CategoryDailyStatus
    irregular: CategoryDailyStatus


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


# ---------------------------------------------------------------------------
# Phrasal Verb Exercise DTOs
# ---------------------------------------------------------------------------

class PhrasalVerbExerciseResponse(BaseModel):
    """Exercise response for phrasal verb training."""

    phrasal_verb_id: int
    exercise_type: int = Field(..., ge=1, le=6)
    phrase: str  # "look up"
    base_verb: str  # "look"
    particle: str  # "up"
    translations: list[str] = []
    definitions: list[dict] = []  # [{"en": "...", "ru": "..."}]
    is_separable: bool = True
    options: list[str] | None = None
    sentence_en: str | None = None
    sentence_ru: str | None = None
    hint: str | None = None
    particle_options: list[str] | None = None  # For particle fill exercises
    separability_options: list[str] | None = None  # For separability exercises


class PhrasalVerbAnswerSubmit(BaseModel):
    phrasal_verb_id: int
    answer: str
    response_time_ms: int = Field(..., ge=0)
    exercise_type: int = Field(default=2, ge=1, le=6)


class PhrasalVerbAnswerResult(BaseModel):
    correct: bool
    rating: int = Field(..., ge=0, le=5)
    correct_answer: str
    feedback: str | None = None
    mastery_level: int
    level_changed: bool


class PhrasalVerbSessionResponse(BaseModel):
    session_id: int
    exercises: list[PhrasalVerbExerciseResponse]
    total_items: int
    daily_limit_warning: bool = False


# ---------------------------------------------------------------------------
# Irregular Verb Exercise DTOs
# ---------------------------------------------------------------------------

class IrregularVerbExerciseResponse(BaseModel):
    """Exercise response for irregular verb training."""

    irregular_verb_id: int
    exercise_type: int = Field(..., ge=1, le=6)
    base_form: str  # "go"
    past_simple: str  # "went"
    past_participle: str  # "gone"
    translations: list[str] = []
    verb_pattern: str = ""  # "ABC", "ABB", "AAA", "ABA"
    transcription_base: str | None = None
    transcription_past: str | None = None
    transcription_participle: str | None = None
    options: list[str] | None = None
    sentence_en: str | None = None
    sentence_ru: str | None = None
    hint: str | None = None
    target_form: str | None = None  # Which form to guess: "base", "past", "participle"
    given_form: str | None = None  # The form shown to user


class IrregularVerbAnswerSubmit(BaseModel):
    irregular_verb_id: int
    answer: str
    response_time_ms: int = Field(..., ge=0)
    exercise_type: int = Field(default=2, ge=1, le=6)


class IrregularVerbAnswerResult(BaseModel):
    correct: bool
    rating: int = Field(..., ge=0, le=5)
    correct_answer: str
    feedback: str | None = None
    mastery_level: int
    level_changed: bool


class IrregularVerbSessionResponse(BaseModel):
    session_id: int
    exercises: list[IrregularVerbExerciseResponse]
    total_items: int
    daily_limit_warning: bool = False


# Rebuild models to resolve forward references
ExercisePhase.model_rebuild()
StartSessionResponse.model_rebuild()
