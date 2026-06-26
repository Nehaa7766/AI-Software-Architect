"""Persistence for User rows. The only layer that touches the User table."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuthProvider, User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str | None,
        provider: AuthProvider = AuthProvider.LOCAL,
        email_verified: bool = False,
        profile_image: str | None = None,
    ) -> User:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            password_hash=password_hash,
            provider=provider,
            email_verified=email_verified,
            profile_image=profile_image,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user
