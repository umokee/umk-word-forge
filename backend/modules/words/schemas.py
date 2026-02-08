from pydantic import BaseModel, Field


class WordContextResponse(BaseModel):
    id: int
    word_id: int
    sentence_en: str
    sentence_ru: str | None = None
    source: str | None = None
    difficulty: int = 1

    model_config = {"from_attributes": True}


class WordResponse(BaseModel):
    id: int
    english: str
    transcription: str | None = None
    part_of_speech: str | None = None
    translations: list[str] = []
    frequency_rank: int | None = None
    cefr_level: str | None = None
    contexts: list[WordContextResponse] = []

    model_config = {"from_attributes": True}


class WordListResponse(BaseModel):
    id: int
    english: str
    transcription: str | None = None
    part_of_speech: str | None = None
    translations: list[str] = []
    frequency_rank: int | None = None
    cefr_level: str | None = None

    model_config = {"from_attributes": True}


class WordCreate(BaseModel):
    english: str = Field(..., min_length=1, max_length=200)
    transcription: str | None = None
    part_of_speech: str | None = None
    translations: list[str] = []
    frequency_rank: int | None = None
    cefr_level: str | None = None


class WordSearch(BaseModel):
    q: str = Field(..., min_length=1, max_length=200)


class PaginatedWords(BaseModel):
    items: list[WordListResponse]
    total: int
    page: int
    per_page: int
