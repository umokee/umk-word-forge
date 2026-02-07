from backend.core.exceptions import AppException, NotFoundError


class WordNotFoundError(NotFoundError):
    def __init__(self, word_id: int | None = None):
        detail = f"Word with id={word_id} not found" if word_id else "Word not found"
        super().__init__(message=detail)


class WordAlreadyExistsError(AppException):
    def __init__(self, english: str):
        super().__init__(
            message=f"Word '{english}' already exists",
            status_code=409,
        )
