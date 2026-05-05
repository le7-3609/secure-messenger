class AppError(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConflictError(AppError):
    """Raised when a resource already exists (e.g. duplicate username)."""


class AuthenticationError(AppError):
    """Raised when credentials are invalid or token cannot be validated."""
