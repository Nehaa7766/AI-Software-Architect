"""Aggregate the analysis module router."""
from fastapi import APIRouter

from app.modules.analysis.controllers import file_controller, symbol_controller

router = APIRouter()
router.include_router(symbol_controller.router)
router.include_router(file_controller.router)
