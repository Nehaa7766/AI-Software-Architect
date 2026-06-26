"""Pydantic request schemas — server-side validation for every auth endpoint.

Never trust the client; these run on every request regardless of frontend checks.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

NAME = Field(min_length=1, max_length=100)
PASSWORD = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    first_name: str = NAME
    last_name: str = NAME
    email: EmailStr
    password: str = PASSWORD
    confirm_password: str

    @field_validator("first_name", "last_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def _passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=10)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    password: str = PASSWORD
    confirm_password: str

    @model_validator(mode="after")
    def _passwords_match(self) -> "ResetPasswordRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = PASSWORD
    confirm_password: str

    @model_validator(mode="after")
    def _passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class UpdateProfileRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
