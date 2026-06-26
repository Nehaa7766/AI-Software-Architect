"""Opaque-token helpers: generate a random token and hash it for storage."""
import hashlib
import secrets


def generate_token(nbytes: int = 48) -> str:
    """Return a URL-safe random token (the raw value sent to the client)."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """SHA-256 hex digest stored in the DB. Lookups hash the incoming token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
