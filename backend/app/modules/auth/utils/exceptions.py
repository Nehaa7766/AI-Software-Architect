"""Domain exceptions for the auth module, mapped to HTTP responses centrally."""


class AuthError(Exception):
    """Base auth error carrying an HTTP status and safe client message."""

    status_code: int = 400
    code: str = "auth_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Authentication error"
        super().__init__(self.message)


class InvalidCredentials(AuthError):
    """Invalid email or password."""

    status_code = 401
    code = "invalid_credentials"


class EmailAlreadyExists(AuthError):
    """An account with this email already exists."""

    status_code = 409
    code = "email_exists"


class InvalidToken(AuthError):
    """The token is invalid, expired, or already used."""

    status_code = 400
    code = "invalid_token"


class TokenReuseDetected(AuthError):
    """Refresh token reuse detected; the session has been revoked."""

    status_code = 401
    code = "token_reuse"


class NotAuthenticated(AuthError):
    """Authentication required."""

    status_code = 401
    code = "not_authenticated"


class PermissionDenied(AuthError):
    """You do not have permission to perform this action."""

    status_code = 403
    code = "permission_denied"


class ValidationError(AuthError):
    """Validation failed."""

    status_code = 422
    code = "validation_error"
