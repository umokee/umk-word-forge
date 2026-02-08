from backend.core.exceptions import AppException, NotFoundError


class WordNotInLearningError(NotFoundError):
    def __init__(self, word_id: int | None = None):
        detail = (
            f"Word with id={word_id} is not in the learning list"
            if word_id
            else "Word is not in the learning list"
        )
        super().__init__(message=detail)


class WordAlreadyInLearningError(AppException):
    def __init__(self, word_id: int):
        super().__init__(
            message=f"Word with id={word_id} is already in the learning list",
            status_code=409,
        )
