"""Auth dependencies + cookie/CSRF helpers shared across controllers."""
import secrets
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.modules.auth.dependencies import get_token_service, get_user_repository
from app.modules.auth.repositories.user_repository import UserRepository
from app.modules.auth.services.token_service import TokenService
from app.modules.auth.utils.exceptions import InvalidToken


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    token_service: TokenService = Depends(get_token_service),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    """Resolve the authenticated user from the Bearer access token."""
    token = _bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = token_service.decode_access_token(token)
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await users.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ---- Refresh cookie helpers ----
def set_refresh_cookie(response: Response, raw_token: str, max_age_seconds: int) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN or None,
        path=settings.API_PREFIX + "/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN or None,
        path=settings.API_PREFIX + "/auth",
    )


def get_refresh_cookie(
    refresh_token: Annotated[str | None, Cookie(alias=settings.REFRESH_COOKIE_NAME)] = None,
) -> str | None:
    return refresh_token


# ---- CSRF (double-submit cookie) for cookie-based mutations ----
def issue_csrf_token(response: Response) -> str:
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=token,
        httponly=False,  # readable by JS so the client can echo it in a header
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN or None,
        path="/",
    )
    return token


def verify_csrf(
    request: Request,
    x_csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    """Double-submit check: header must match the non-HttpOnly CSRF cookie."""
    cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    if not cookie_token or not x_csrf_token or not secrets.compare_digest(
        cookie_token, x_csrf_token
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed."
        )
