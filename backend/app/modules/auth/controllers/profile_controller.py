"""HTTP handlers for the authenticated user's profile."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.security import CurrentUser
from app.modules.auth.dependencies import get_profile_service
from app.modules.auth.dto.responses import MessageResponse, UserResponse
from app.modules.auth.services.profile_service import ProfileService
from app.modules.auth.validators.schemas import (
    ChangePasswordRequest,
    UpdateProfileRequest,
)

router = APIRouter(prefix="/profile", tags=["profile"])

ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


@router.get("", response_model=UserResponse)
async def view_profile(current_user: CurrentUser) -> UserResponse:
    return UserResponse.from_user(current_user)


@router.patch("", response_model=UserResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: CurrentUser,
    service: ProfileServiceDep,
) -> UserResponse:
    user = await service.update_profile(
        current_user,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return UserResponse.from_user(user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    service: ProfileServiceDep,
) -> MessageResponse:
    await service.change_password(
        current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return MessageResponse(message="Password changed. Please log in again.")


@router.post("/avatar", response_model=UserResponse)
async def upload_avatar(
    current_user: CurrentUser,
    service: ProfileServiceDep,
    file: Annotated[UploadFile, File()],
) -> UserResponse:
    data = await file.read()
    user = await service.save_avatar(
        current_user, content_type=file.content_type or "", data=data
    )
    return UserResponse.from_user(user)
