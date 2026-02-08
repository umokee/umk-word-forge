from pydantic import BaseModel
from datetime import datetime


class SubmitAnswerResult(BaseModel):
    correct: bool
    rating: int
    correct_answer: str
    feedback: str | None = None
    mastery_level: int
    level_changed: bool
    next_review: datetime | None = None
    session_progress: dict | None = None


class StartSessionResult(BaseModel):
    session_id: int
    exercises: list[dict]
    total_words: int


class AddWordResult(BaseModel):
    word_id: int
    english: str
    added_to_learning: bool
    contexts_generated: int
