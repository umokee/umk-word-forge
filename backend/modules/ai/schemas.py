from pydantic import BaseModel, Field


class AICheckRequest(BaseModel):
    word: str
    translation: str
    sentence: str


class AICheckResult(BaseModel):
    correct: bool
    grammar_ok: bool
    word_usage_ok: bool
    natural: bool
    feedback_ru: str
    corrected: str | None = None


class AIContextRequest(BaseModel):
    word: str
    part_of_speech: str
    count: int = Field(default=3, ge=1, le=10)


class AIContextResult(BaseModel):
    contexts: list[dict]


class AIEnrichResult(BaseModel):
    verb_forms: dict | None = None
    collocations: list[dict] = []
    phrasal_verbs: list[dict] | None = None
    usage_notes: list[str] = []
    common_mistakes: list[dict] = []
