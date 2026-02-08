from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.modules.learning.schemas import (
    UserWordWithWord,
    ReviewCreate,
    ReviewResponse,
    MasteryResult,
    LearningStatsResponse,
    DueWordsResponse,
    PaginatedUserWords,
)
from backend.modules.learning.service import LearningService

router = APIRouter(prefix="/api/learning", tags=["learning"])

_service = LearningService()


@router.get("/words", response_model=PaginatedUserWords)
def list_user_words(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    level: int | None = Query(None, ge=0, le=7),
    state: int | None = Query(None, ge=0, le=3),
    db: Session = Depends(get_db),
):
    return _service.get_user_words(
        db,
        page=page,
        per_page=per_page,
        level=level,
        state=state,
    )


@router.get("/words/{word_id}", response_model=UserWordWithWord)
def get_user_word(
    word_id: int,
    db: Session = Depends(get_db),
):
    return _service.get_user_word(db, word_id)


@router.get("/due", response_model=DueWordsResponse)
def get_due_words(
    db: Session = Depends(get_db),
):
    return _service.get_due_words(db)


@router.get("/stats", response_model=LearningStatsResponse)
def get_learning_stats(
    db: Session = Depends(get_db),
):
    return _service.get_learning_stats(db)


@router.post("/words/{word_id}/initialize", response_model=UserWordWithWord)
def initialize_word(
    word_id: int,
    db: Session = Depends(get_db),
):
    user_word = _service.initialize_word(db, word_id)
    return _service.get_user_word(db, word_id)


@router.post("/words/{word_id}/review", response_model=MasteryResult)
def record_review(
    word_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
):
    return _service.record_review(db, word_id, review)
