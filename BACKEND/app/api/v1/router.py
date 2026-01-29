from fastapi import APIRouter

# Modules
from app.modules.iam.endpoints import router as iam_router
from app.modules.operational.endpoints import router as operational_router

# V1 Endpoints
from app.api.v1.endpoints import (
    predictions,
    alerts,
    routing,
    weather,
    health
)

api_router = APIRouter()

api_router.include_router(iam_router, prefix="/iam", tags=["Identity & Access"])
api_router.include_router(operational_router, prefix="/operational", tags=["Operational"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(routing.router, prefix="/routing", tags=["Routing"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
