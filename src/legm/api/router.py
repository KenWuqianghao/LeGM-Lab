"""Top-level router aggregating all sub-routers."""

from fastapi import APIRouter

from legm.api.bot import router as bot_router
from legm.api.health import router as health_router
from legm.api.takes import router as takes_router

root_router = APIRouter()
root_router.include_router(health_router)
root_router.include_router(takes_router)
root_router.include_router(bot_router)
