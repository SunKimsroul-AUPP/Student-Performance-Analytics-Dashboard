class AppError(Exception):
    """Base application error."""


class DataValidationError(AppError):
    """Raised when data validation fails."""