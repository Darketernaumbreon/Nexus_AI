from fastapi import APIRouter
from .endpoints import predictions
from .endpoints import alerts
from .endpoints import routing
from .endpoints import health
from app.modules.iam.endpoints import router as iam_router
from app.modules.operational.endpoints import router as operational_router

api_router = APIRouter()
api_router.include_router(iam_router, prefix="/iam", tags=["iam"])
api_router.include_router(operational_router, prefix="/operational", tags=["operational"])
api_router.include_router(predictions.router, prefix="/predict", tags=["predictions"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(routing.router, prefix="/routing", tags=["routing"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
