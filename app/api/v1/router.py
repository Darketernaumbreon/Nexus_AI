from fastapi import APIRouter
from app.api.v1.endpoints import predictions
from app.modules.iam import endpoints as login_endpoints

api_router = APIRouter()

api_router.include_router(login_endpoints.router, tags=["login"])
api_router.include_router(predictions.router, prefix="/predict", tags=["predictions"])
