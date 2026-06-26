"""Persistence for refresh / password-reset / email-verification tokens.

All tokens are stored as SHA-256 hashes; callers pass the already-hashed value.
"""
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import (
    AuthAuditLog,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)


class TokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Refresh tokens ----
    async def add_refresh(
        self, *, user_id: str, token_hash: str, family_id: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh(self, token: RefreshToken) -> None:
        token.revoked = True
        await self.db.flush()

    async def revoke_family(self, family_id: str) -> None:
        """Revoke every token in a rotation chain (theft response)."""
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .values(revoked=True)
        )
        await self.db.flush()

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self.db.flush()

    # ---- Password reset tokens ----
    async def add_reset(
        self, *, user_id: str, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_reset(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_reset_used(self, token: PasswordResetToken, used_at: datetime) -> None:
        token.used_at = used_at
        await self.db.flush()

    # ---- Email verification tokens ----
    async def add_verification(
        self, *, user_id: str, token_hash: str, expires_at: datetime
    ) -> EmailVerificationToken:
        token = EmailVerificationToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_verification(self, token_hash: str) -> EmailVerificationToken | None:
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    async def mark_verification_used(
        self, token: EmailVerificationToken, used_at: datetime
    ) -> None:
        token.used_at = used_at
        await self.db.flush()

    # ---- Audit log ----
    async def add_audit(
        self,
        *,
        event: str,
        user_id: str | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.db.add(
            AuthAuditLog(event=event, user_id=user_id, ip=ip, user_agent=user_agent)
        )
        await self.db.flush()
