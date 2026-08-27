"""API v1 master router aggregating all sub-routes."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.reconciliation import router as reconciliation_router

api_v1_router = APIRouter()

# Include health router
api_v1_router.include_router(health_router)

# Include reconciliation router
api_v1_router.include_router(reconciliation_router)
