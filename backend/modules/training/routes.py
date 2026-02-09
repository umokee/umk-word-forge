from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Literal

from backend.core.database import get_db

from . import service
from . import phrasal_service
from . import irregular_service
from . import daily_limit_service
from .context_service import ensure_ai_contexts, enrich_word_data, ensure_rich_contexts
from .schemas import (
    AnswerResult,
    AnswerSubmit,
    DailyStatusResponse,
    CategoryDailyStatus,
    SessionCreate,
    SessionProgress,
    SessionResponse,
    SessionSummary,
    StartSessionResponse,
    PhrasalVerbAnswerResult,
    PhrasalVerbAnswerSubmit,
    PhrasalVerbSessionResponse,
    IrregularVerbAnswerResult,
    IrregularVerbAnswerSubmit,
    IrregularVerbSessionResponse,
)

router = APIRouter(prefix="/api/training", tags=["training"])


@router.get("/daily-status", response_model=DailyStatusResponse)
def get_daily_status(
    db: Session = Depends(get_db),
) -> DailyStatusResponse:
    """Get daily training status for all categories."""
    status = daily_limit_service.get_all_categories_status(db)
    return DailyStatusResponse(
        words=CategoryDailyStatus(**status["words"]),
        phrasal=CategoryDailyStatus(**status["phrasal"]),
        irregular=CategoryDailyStatus(**status["irregular"]),
    )


@router.post("/session", response_model=StartSessionResponse, status_code=201)
async def start_session(
    body: SessionCreate | None = None,
    db: Session = Depends(get_db),
) -> StartSessionResponse:
    """Start a new training session with exercises."""
    # Check daily limit (soft - just adds warning)
    limit_status = daily_limit_service.check_daily_limit(db, "words")

    duration = body.duration_minutes if body else 15
    result = service.create_session(db, duration_minutes=duration)

    # Record session start for daily tracking
    daily_limit_service.record_session_start(db, "words", result.session_id)

    # Add daily limit warning to response
    result.daily_limit_warning = limit_status["exceeded"]

    # Generate AI contexts and enrich words (async)
    for exercise in result.exercises:
        # Try rich contexts first (handles function words specially)
        rich_data = await ensure_rich_contexts(db, exercise.word_id)
        if rich_data:
            # Update exercise with function word data
            exercise.is_function_word = True
            exercise.usage_rules = rich_data.get("usage_rules")
            exercise.comparisons = rich_data.get("comparisons")
            exercise.common_errors = rich_data.get("common_errors")
        else:
            # Regular word - use standard context generation
            await ensure_ai_contexts(db, exercise.word_id)
        await enrich_word_data(db, exercise.word_id)

    # Refresh exercises with new contexts
    result = service.refresh_session_contexts(db, result)

    return result


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
    result = service.end_session(db, session_id)

    # Record session completion for daily tracking
    daily_limit_service.record_session_complete(db, session_id)

    return result


# ---------------------------------------------------------------------------
# Phrasal Verb Training Routes
# ---------------------------------------------------------------------------

@router.post("/session/phrasal", response_model=PhrasalVerbSessionResponse, status_code=201)
async def start_phrasal_session(
    body: SessionCreate | None = None,
    db: Session = Depends(get_db),
) -> PhrasalVerbSessionResponse:
    """Start a new training session for phrasal verbs."""
    # Check daily limit (soft - just adds warning)
    limit_status = daily_limit_service.check_daily_limit(db, "phrasal")

    duration = body.duration_minutes if body else 15
    result = phrasal_service.create_phrasal_verb_session(db, duration_minutes=duration)

    # Record session start for daily tracking
    daily_limit_service.record_session_start(db, "phrasal", result.session_id)

    # Add daily limit warning to response
    result.daily_limit_warning = limit_status["exceeded"]

    return result


@router.post(
    "/session/{session_id}/phrasal/answer",
    response_model=PhrasalVerbAnswerResult,
)
def submit_phrasal_answer(
    session_id: int,
    body: PhrasalVerbAnswerSubmit,
    db: Session = Depends(get_db),
) -> PhrasalVerbAnswerResult:
    """Submit an answer for a phrasal verb exercise."""
    return phrasal_service.record_phrasal_verb_answer(db, session_id, body)


# ---------------------------------------------------------------------------
# Irregular Verb Training Routes
# ---------------------------------------------------------------------------

@router.post("/session/irregular", response_model=IrregularVerbSessionResponse, status_code=201)
async def start_irregular_session(
    body: SessionCreate | None = None,
    db: Session = Depends(get_db),
) -> IrregularVerbSessionResponse:
    """Start a new training session for irregular verbs."""
    # Check daily limit (soft - just adds warning)
    limit_status = daily_limit_service.check_daily_limit(db, "irregular")

    duration = body.duration_minutes if body else 15
    result = irregular_service.create_irregular_verb_session(db, duration_minutes=duration)

    # Record session start for daily tracking
    daily_limit_service.record_session_start(db, "irregular", result.session_id)

    # Add daily limit warning to response
    result.daily_limit_warning = limit_status["exceeded"]

    return result


@router.post(
    "/session/{session_id}/irregular/answer",
    response_model=IrregularVerbAnswerResult,
)
def submit_irregular_answer(
    session_id: int,
    body: IrregularVerbAnswerSubmit,
    db: Session = Depends(get_db),
) -> IrregularVerbAnswerResult:
    """Submit an answer for an irregular verb exercise."""
    return irregular_service.record_irregular_verb_answer(db, session_id, body)
