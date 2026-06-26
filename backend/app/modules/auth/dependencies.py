"""FastAPI dependency providers that wire repositories + services per request.

Keeps controllers thin and makes the dependency graph explicit (DIP).
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.repositories.token_repository import TokenRepository
from app.modules.auth.repositories.user_repository import UserRepository
from app.modules.auth.services.auth_service import AuthService
from app.modules.auth.services.google_service import google_service
from app.modules.auth.services.mail_service import mail_service
from app.modules.auth.services.password_service import password_service
from app.modules.auth.services.profile_service import ProfileService
from app.modules.auth.services.token_service import TokenService

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_token_repository(db: DbSession) -> TokenRepository:
    return TokenRepository(db)


def get_token_service(
    tokens: Annotated[TokenRepository, Depends(get_token_repository)],
) -> TokenService:
    return TokenService(tokens)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    tokens: Annotated[TokenRepository, Depends(get_token_repository)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> AuthService:
    return AuthService(
        users=users,
        tokens=tokens,
        token_service=token_service,
        password_service=password_service,
        google_service=google_service,
        mail_service=mail_service,
    )


def get_profile_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    tokens: Annotated[TokenRepository, Depends(get_token_repository)],
) -> ProfileService:
    return ProfileService(
        users=users, tokens=tokens, password_service=password_service
    )
