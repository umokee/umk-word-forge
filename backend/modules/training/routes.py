from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db

from . import service
from .schemas import (
    AnswerResult,
    AnswerSubmit,
    SessionCreate,
    SessionProgress,
    SessionResponse,
    SessionSummary,
)

router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("/session", response_model=SessionResponse, status_code=201)
def start_session(
    body: SessionCreate | None = None,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Start a new training session."""
    return service.create_session(db)


@router.get("/session/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Return information about a training session."""
    return service.get_session(db, session_id)


@router.get("/session/{session_id}/progress", response_model=SessionProgress)
def get_progress(
    session_id: int,
    db: Session = Depends(get_db),
) -> SessionProgress:
    """Return live progress for an active session."""
    return service.get_progress(db, session_id)


@router.post("/session/{session_id}/answer", response_model=AnswerResult)
def submit_answer(
    session_id: int,
    body: AnswerSubmit,
    db: Session = Depends(get_db),
) -> AnswerResult:
    """Submit an answer for the current exercise."""
    return service.record_answer(db, session_id, body)


@router.post("/session/{session_id}/end", response_model=SessionSummary)
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> SessionSummary:
    """Finalize the training session and return a summary."""
    return service.end_session(db, session_id)
