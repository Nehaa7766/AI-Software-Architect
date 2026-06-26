"""Argon2id password hashing and strength validation."""
import re

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.modules.auth.utils.exceptions import ValidationError

# Argon2id with sensible defaults (OWASP-aligned); tune cost for your hardware.
_hasher = PasswordHasher(
    time_cost=3, memory_cost=64 * 1024, parallelism=4, hash_len=32, salt_len=16
)

_MIN_LENGTH = 8


class PasswordService:
    def hash(self, password: str) -> str:
        return _hasher.hash(password)

    def verify(self, password: str, password_hash: str | None) -> bool:
        if not password_hash:
            return False
        try:
            return _hasher.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        return _hasher.check_needs_rehash(password_hash)

    def validate_strength(self, password: str) -> None:
        """Raise ValidationError if the password is too weak.

        Server-side enforcement — never rely on the client. Mirrors the Zod
        rules on the frontend.
        """
        problems: list[str] = []
        if len(password) < _MIN_LENGTH:
            problems.append(f"at least {_MIN_LENGTH} characters")
        if not re.search(r"[a-z]", password):
            problems.append("a lowercase letter")
        if not re.search(r"[A-Z]", password):
            problems.append("an uppercase letter")
        if not re.search(r"\d", password):
            problems.append("a number")
        if not re.search(r"[^A-Za-z0-9]", password):
            problems.append("a special character")
        if problems:
            raise ValidationError("Password must contain " + ", ".join(problems) + ".")


password_service = PasswordService()
