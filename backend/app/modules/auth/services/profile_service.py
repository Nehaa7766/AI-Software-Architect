"""Profile operations: update details, change password, store avatar."""
import os
import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings
from app.models.user import User
from app.modules.auth.repositories.token_repository import TokenRepository
from app.modules.auth.repositories.user_repository import UserRepository
from app.modules.auth.services.password_service import PasswordService
from app.modules.auth.utils.exceptions import InvalidCredentials, ValidationError

_ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class ProfileService:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: TokenRepository,
        password_service: PasswordService,
    ) -> None:
        self.users = users
        self.tokens = tokens
        self.passwords = password_service

    async def update_profile(
        self, user: User, *, first_name: str | None, last_name: str | None
    ) -> User:
        fields = {}
        if first_name is not None:
            fields["first_name"] = first_name
        if last_name is not None:
            fields["last_name"] = last_name
        if fields:
            user = await self.users.update(user, **fields)
        return user

    async def change_password(
        self, user: User, *, current_password: str, new_password: str
    ) -> None:
        if not self.passwords.verify(current_password, user.password_hash):
            raise InvalidCredentials("Current password is incorrect.")
        self.passwords.validate_strength(new_password)
        await self.users.update(user, password_hash=self.passwords.hash(new_password))
        # Revoke other sessions after a password change.
        await self.tokens.revoke_all_for_user(user.id)
        await self.tokens.add_audit(event="PASSWORD_CHANGED", user_id=user.id)

    async def save_avatar(
        self, user: User, *, content_type: str, data: bytes
    ) -> User:
        ext = _ALLOWED_IMAGE_TYPES.get(content_type)
        if ext is None:
            raise ValidationError("Avatar must be a JPEG, PNG, or WebP image.")
        if len(data) > settings.MAX_AVATAR_BYTES:
            raise ValidationError("Avatar exceeds the maximum allowed size.")

        upload_dir = Path(settings.UPLOAD_DIR) / "avatars"
        upload_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{user.id}_{uuid.uuid4().hex}{ext}"
        path = upload_dir / filename
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)

        public_url = f"/uploads/avatars/{filename}"
        return await self.users.update(user, profile_image=public_url)
