"""Aggregate auth + profile routers under a single module router."""
from fastapi import APIRouter

from app.modules.auth.controllers import auth_controller, profile_controller

router = APIRouter()
router.include_router(auth_controller.router)
router.include_router(profile_controller.router)
