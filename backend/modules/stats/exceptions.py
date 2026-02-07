from backend.core.exceptions import AppException


class StatsNotFoundError(AppException):
    def __init__(self, message: str = "Stats not found"):
        super().__init__(message, status_code=404)


class StatsCalculationError(AppException):
    def __init__(self, message: str = "Error calculating stats"):
        super().__init__(message, status_code=500)
