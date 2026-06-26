"""Core auth orchestration: register, login, Google, refresh, logout, reset.

Coordinates the repositories + password/token/mail/google services. Returns
plain data (User + raw tokens); HTTP concerns (cookies, status) live in the
controller.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models.user import AuthProvider, User
from app.modules.auth.repositories.token_repository import TokenRepository
from app.modules.auth.repositories.user_repository import UserRepository
from app.modules.auth.services.audit_service import record_audit
from app.modules.auth.services.google_service import GoogleService
from app.modules.auth.services.mail_service import MailService
from app.modules.auth.services.password_service import PasswordService
from app.modules.auth.services.token_service import IssuedRefresh, TokenService
from app.modules.auth.utils.exceptions import (
    EmailAlreadyExists,
    InvalidCredentials,
    InvalidToken,
)
from app.modules.auth.utils.tokens import generate_token, hash_token


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AuthResult:
    user: User
    access_token: str
    refresh: IssuedRefresh


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: TokenRepository,
        token_service: TokenService,
        password_service: PasswordService,
        google_service: GoogleService,
        mail_service: MailService,
    ) -> None:
        self.users = users
        self.tokens = tokens
        self.token_service = token_service
        self.passwords = password_service
        self.google = google_service
        self.mail = mail_service

    async def _issue_session(self, user: User) -> AuthResult:
        access = self.token_service.create_access_token(user)
        refresh = await self.token_service.issue_refresh_token(user)
        return AuthResult(user=user, access_token=access, refresh=refresh)

    # ---- Registration ----
    async def register(
        self, *, first_name: str, last_name: str, email: str, password: str
    ) -> AuthResult:
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise EmailAlreadyExists()

        self.passwords.validate_strength(password)
        user = await self.users.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=self.passwords.hash(password),
            provider=AuthProvider.LOCAL,
            email_verified=False,
        )
        await self._send_verification_email(user)
        await self.tokens.add_audit(event="REGISTER", user_id=user.id)
        return await self._issue_session(user)

    # ---- Email + password login ----
    async def login(self, *, email: str, password: str) -> AuthResult:
        user = await self.users.get_by_email(email)
        # Constant-ish behaviour + generic error to avoid user enumeration.
        if user is None or not self.passwords.verify(password, user.password_hash):
            # Written in its own committed session — the request rolls back on raise.
            await record_audit(event="LOGIN_FAIL", user_id=user.id if user else None)
            raise InvalidCredentials()

        if self.passwords.needs_rehash(user.password_hash or ""):
            await self.users.update(
                user, password_hash=self.passwords.hash(password)
            )

        await self.tokens.add_audit(event="LOGIN_SUCCESS", user_id=user.id)
        return await self._issue_session(user)

    # ---- Google login ----
    async def login_with_google(self, *, id_token: str) -> AuthResult:
        profile = self.google.verify(id_token)
        user = await self.users.get_by_email(profile.email)

        if user is None:
            user = await self.users.create(
                first_name=profile.first_name,
                last_name=profile.last_name,
                email=profile.email,
                password_hash=None,
                provider=AuthProvider.GOOGLE,
                email_verified=profile.email_verified,
                profile_image=profile.picture,
            )
            await self.tokens.add_audit(event="REGISTER_GOOGLE", user_id=user.id)
        elif user.provider == AuthProvider.LOCAL:
            # Link the existing local account to Google; verify email via Google.
            await self.users.update(
                user,
                provider=AuthProvider.GOOGLE,
                email_verified=user.email_verified or profile.email_verified,
                profile_image=user.profile_image or profile.picture,
            )
            await self.tokens.add_audit(event="LINK_GOOGLE", user_id=user.id)

        await self.tokens.add_audit(event="LOGIN_SUCCESS", user_id=user.id)
        return await self._issue_session(user)

    # ---- Refresh ----
    async def refresh(self, raw_refresh: str) -> AuthResult:
        user_id, new_refresh = await self.token_service.rotate_refresh_token(raw_refresh)
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise InvalidToken("User no longer exists.")
        access = self.token_service.create_access_token(user)
        return AuthResult(user=user, access_token=access, refresh=new_refresh)

    # ---- Logout ----
    async def logout(self, raw_refresh: str | None) -> None:
        if raw_refresh:
            record = await self.token_service.revoke_refresh_token(raw_refresh)
            if record:
                await self.tokens.add_audit(event="LOGOUT", user_id=record.user_id)

    # ---- Forgot / reset password ----
    async def request_password_reset(self, *, email: str, reset_base_url: str) -> None:
        """Always succeeds from the caller's view (no user enumeration)."""
        user = await self.users.get_by_email(email)
        if user is None or user.provider == AuthProvider.GOOGLE:
            return
        raw = generate_token()
        expires_at = _now() + timedelta(minutes=settings.RESET_TOKEN_TTL_MINUTES)
        await self.tokens.add_reset(
            user_id=user.id, token_hash=hash_token(raw), expires_at=expires_at
        )
        await self.mail.send_password_reset(
            to=user.email, reset_link=f"{reset_base_url}?token={raw}"
        )
        await self.tokens.add_audit(event="PASSWORD_RESET_REQUEST", user_id=user.id)

    async def reset_password(self, *, token: str, new_password: str) -> None:
        record = await self.tokens.get_reset(hash_token(token))
        if record is None or record.used_at is not None:
            raise InvalidToken("Reset link is invalid or already used.")
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < _now():
            raise InvalidToken("Reset link has expired.")

        self.passwords.validate_strength(new_password)
        user = await self.users.get_by_id(record.user_id)
        if user is None:
            raise InvalidToken("User no longer exists.")

        await self.users.update(user, password_hash=self.passwords.hash(new_password))
        await self.tokens.mark_reset_used(record, _now())
        # Reset = revoke all sessions so a thief is logged out everywhere.
        await self.tokens.revoke_all_for_user(user.id)
        await self.tokens.add_audit(event="PASSWORD_RESET", user_id=user.id)

    # ---- Email verification ----
    async def _send_verification_email(self, user: User) -> None:
        raw = generate_token()
        expires_at = _now() + timedelta(hours=settings.VERIFY_TOKEN_TTL_HOURS)
        await self.tokens.add_verification(
            user_id=user.id, token_hash=hash_token(raw), expires_at=expires_at
        )
        verify_link = f"{settings.CLIENT_ORIGIN}/verify-email?token={raw}"
        await self.mail.send_verification(to=user.email, verify_link=verify_link)

    async def verify_email(self, *, token: str) -> None:
        record = await self.tokens.get_verification(hash_token(token))
        if record is None or record.used_at is not None:
            raise InvalidToken("Verification link is invalid or already used.")
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < _now():
            raise InvalidToken("Verification link has expired.")
        user = await self.users.get_by_id(record.user_id)
        if user is None:
            raise InvalidToken("User no longer exists.")
        await self.users.update(user, email_verified=True)
        await self.tokens.mark_verification_used(record, _now())
        await self.tokens.add_audit(event="EMAIL_VERIFIED", user_id=user.id)
