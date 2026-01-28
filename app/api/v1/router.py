from fastapi import APIRouter
from app.api.v1.endpoints import predictions
from app.api.v1.endpoints import alerts
from app.api.v1.endpoints import routing
from app.modules.iam.endpoints import router as iam_router
from app.modules.operational.endpoints import router as operational_router
from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(iam_router, prefix="/iam", tags=["iam"])
api_router.include_router(operational_router, prefix="/operational", tags=["operational"])
api_router.include_router(predictions.router, prefix="/predict", tags=["predictions"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(routing.router, prefix="/routing", tags=["routing"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
