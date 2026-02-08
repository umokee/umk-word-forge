"""Training module -- public API.

Import the router to register endpoints and the model for Alembic discovery.
"""

from .routes import router
from .models import TrainingSession
from .schemas import (
    AnswerResult,
    AnswerSubmit,
    ExerciseResponse,
    SessionCreate,
    SessionProgress,
    SessionResponse,
    SessionSummary,
)
from .exceptions import SessionAlreadyEndedError, SessionNotFoundError

__all__ = [
    "router",
    "TrainingSession",
    "AnswerResult",
    "AnswerSubmit",
    "ExerciseResponse",
    "SessionCreate",
    "SessionProgress",
    "SessionResponse",
    "SessionSummary",
    "SessionAlreadyEndedError",
    "SessionNotFoundError",
]
