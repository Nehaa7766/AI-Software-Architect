"""HTTP handlers for authentication endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import (
    CurrentUser,
    clear_refresh_cookie,
    get_refresh_cookie,
    issue_csrf_token,
    set_refresh_cookie,
)
from app.modules.auth.dependencies import get_auth_service
from app.modules.auth.dto.responses import AuthResponse, MessageResponse, UserResponse
from app.modules.auth.services.auth_service import AuthResult, AuthService
from app.modules.auth.validators.schemas import (
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
_REFRESH_MAX_AGE = settings.REFRESH_TOKEN_TTL_DAYS * 24 * 3600


def _finish_session(result: AuthResult, response: Response) -> AuthResponse:
    """Attach the rotating refresh cookie + CSRF token, return the body."""
    set_refresh_cookie(response, result.refresh.raw, _REFRESH_MAX_AGE)
    issue_csrf_token(response)
    return AuthResponse(
        user=UserResponse.from_user(result.user), access_token=result.access_token
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    payload: RegisterRequest,
    response: Response,
    service: AuthServiceDep,
) -> AuthResponse:
    result = await service.register(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password=payload.password,
    )
    return _finish_session(result, response)


@router.post("/login", response_model=AuthResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    service: AuthServiceDep,
) -> AuthResponse:
    result = await service.login(email=payload.email, password=payload.password)
    return _finish_session(result, response)


@router.post("/google", response_model=AuthResponse)
async def google_login(
    payload: GoogleLoginRequest, response: Response, service: AuthServiceDep
) -> AuthResponse:
    result = await service.login_with_google(id_token=payload.id_token)
    return _finish_session(result, response)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    response: Response,
    service: AuthServiceDep,
    raw_refresh: Annotated[str | None, Depends(get_refresh_cookie)] = None,
) -> AuthResponse:
    from fastapi import HTTPException

    if not raw_refresh:
        raise HTTPException(status_code=401, detail="Missing refresh token.")
    result = await service.refresh(raw_refresh)
    return _finish_session(result, response)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    service: AuthServiceDep,
    raw_refresh: Annotated[str | None, Depends(get_refresh_cookie)] = None,
) -> MessageResponse:
    await service.logout(raw_refresh)
    clear_refresh_cookie(response)
    return MessageResponse(message="Logged out.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit(settings.RATE_LIMIT_FORGOT)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    service: AuthServiceDep,
) -> MessageResponse:
    reset_base_url = f"{settings.CLIENT_ORIGIN}/reset-password"
    await service.request_password_reset(
        email=payload.email, reset_base_url=reset_base_url
    )
    # Always the same response — no account enumeration.
    return MessageResponse(
        message="If an account exists for that email, a reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, service: AuthServiceDep
) -> MessageResponse:
    await service.reset_password(token=payload.token, new_password=payload.password)
    return MessageResponse(message="Password updated. You can now log in.")


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, service: AuthServiceDep) -> MessageResponse:
    await service.verify_email(token=token)
    return MessageResponse(message="Email verified.")


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.from_user(current_user)
