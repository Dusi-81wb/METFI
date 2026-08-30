from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.investigation import router as investigation_router
from app.api.v1.reconciliation import router as reconciliation_router

api_v1_router = APIRouter()

# Include health router
api_v1_router.include_router(health_router)

# Include reconciliation router
api_v1_router.include_router(reconciliation_router)

# Include investigation router
api_v1_router.include_router(investigation_router)
