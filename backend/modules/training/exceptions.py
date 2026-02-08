from backend.core.exceptions import AppException, NotFoundError


class SessionNotFoundError(NotFoundError):
    def __init__(self, session_id: int | None = None):
        detail = (
            f"Training session with id={session_id} not found"
            if session_id
            else "Training session not found"
        )
        super().__init__(message=detail)


class SessionAlreadyEndedError(AppException):
    def __init__(self, session_id: int):
        super().__init__(
            message=f"Training session {session_id} has already ended",
            status_code=409,
        )
