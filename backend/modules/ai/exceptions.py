from backend.core.exceptions import AppException


class AllProvidersFailedError(AppException):
    def __init__(self, message: str = "All AI providers failed"):
        super().__init__(message, status_code=502)


class AIRateLimitError(AppException):
    def __init__(self, message: str = "AI provider rate limit exceeded"):
        super().__init__(message, status_code=429)
