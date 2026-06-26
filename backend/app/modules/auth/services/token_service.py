"""JWT access tokens + opaque rotating refresh tokens.

Access token: signed JWT, short-lived, stateless.
Refresh token: random opaque string. Only its SHA-256 hash is persisted. Each
use rotates (old revoked, new issued in the same family). Reuse of a revoked
token revokes the whole family — theft detection.
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.models.user import RefreshToken, User
from app.modules.auth.repositories.token_repository import TokenRepository
from app.modules.auth.utils.exceptions import InvalidToken, TokenReuseDetected
from app.modules.auth.utils.tokens import generate_token, hash_token


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IssuedRefresh:
    """A freshly issued refresh token: raw value for the client + DB row."""

    def __init__(self, raw: str, expires_at: datetime) -> None:
        self.raw = raw
        self.expires_at = expires_at


class TokenService:
    def __init__(self, tokens: TokenRepository) -> None:
        self.tokens = tokens

    # ---- Access token (JWT) ----
    def create_access_token(self, user: User) -> str:
        now = _now()
        payload = {
            "sub": user.id,
            "email": user.email,
            "provider": user.provider.value,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES)).timestamp()
            ),
        }
        return jwt.encode(
            payload, settings.ACCESS_TOKEN_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.ACCESS_TOKEN_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError as exc:
            raise InvalidToken("Access token is invalid or expired.") from exc
        if payload.get("type") != "access":
            raise InvalidToken("Wrong token type.")
        return payload

    # ---- Refresh token (opaque, rotating) ----
    async def issue_refresh_token(
        self, user: User, *, family_id: str | None = None
    ) -> IssuedRefresh:
        raw = generate_token()
        expires_at = _now() + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)
        await self.tokens.add_refresh(
            user_id=user.id,
            token_hash=hash_token(raw),
            family_id=family_id or str(uuid.uuid4()),
            expires_at=expires_at,
        )
        return IssuedRefresh(raw=raw, expires_at=expires_at)

    async def rotate_refresh_token(self, raw_token: str) -> tuple[str, IssuedRefresh]:
        """Validate + rotate a refresh token. Returns (user_id, new refresh).

        Raises TokenReuseDetected if a revoked token is replayed.
        """
        record = await self.tokens.get_refresh(hash_token(raw_token))
        if record is None:
            raise InvalidToken("Refresh token not recognized.")

        if record.revoked:
            # Replay of an already-rotated token => credential theft. Burn the chain.
            await self.tokens.revoke_family(record.family_id)
            raise TokenReuseDetected()

        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < _now():
            raise InvalidToken("Refresh token expired.")

        await self.tokens.revoke_refresh(record)
        new_raw = generate_token()
        new_expires = _now() + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS)
        await self.tokens.add_refresh(
            user_id=record.user_id,
            token_hash=hash_token(new_raw),
            family_id=record.family_id,
            expires_at=new_expires,
        )
        return record.user_id, IssuedRefresh(raw=new_raw, expires_at=new_expires)

    async def revoke_refresh_token(self, raw_token: str) -> RefreshToken | None:
        record = await self.tokens.get_refresh(hash_token(raw_token))
        if record and not record.revoked:
            await self.tokens.revoke_refresh(record)
        return record
