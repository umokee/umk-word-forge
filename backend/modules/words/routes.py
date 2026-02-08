from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.modules.words.schemas import (
    WordResponse,
    WordListResponse,
    WordCreate,
    PaginatedWords,
)
from backend.modules.words.service import WordService

router = APIRouter(prefix="/api/words", tags=["words"])

_service = WordService()


@router.get("/", response_model=PaginatedWords)
def list_words(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    cefr_level: str | None = Query(None),
    part_of_speech: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return _service.get_words(
        db,
        page=page,
        per_page=per_page,
        search=search,
        cefr_level=cefr_level,
        part_of_speech=part_of_speech,
    )


@router.get("/search", response_model=list[WordListResponse])
def search_words(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    return _service.search_words(db, q)


@router.get("/{word_id}", response_model=WordResponse)
def get_word(
    word_id: int,
    db: Session = Depends(get_db),
):
    return _service.get_word(db, word_id)


@router.post("/", response_model=WordResponse, status_code=201)
def create_word(
    word_create: WordCreate,
    db: Session = Depends(get_db),
):
    return _service.create_word(db, word_create)


@router.delete("/{word_id}", status_code=204)
def delete_word(
    word_id: int,
    db: Session = Depends(get_db),
):
    _service.delete_word(db, word_id)
