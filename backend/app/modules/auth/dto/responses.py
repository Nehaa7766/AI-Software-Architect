"""Response DTOs. ORM objects never cross the HTTP boundary directly."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import AuthProvider, User


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    provider: AuthProvider
    profile_image: str | None
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls.model_validate(user)


class AuthResponse(BaseModel):
    """Returned by register/login/google/refresh. Refresh token is in a cookie."""

    user: UserResponse
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str
