"""Aggregate the projects module router."""
from fastapi import APIRouter

from app.modules.projects.controllers import project_controller, scan_controller

router = APIRouter()
router.include_router(project_controller.router)
router.include_router(scan_controller.router)
