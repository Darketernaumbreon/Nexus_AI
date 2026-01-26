from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.logging import get_logger
from app.core.limiter import limiter

logger = get_logger("main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="NEXUS-AI Backend API - Disaster Risk Prediction & Routing"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint to ensure API is running.
    """
    logger.info("Health check requested")
    return {"status": "ok", "version": "0.1.0"}

if __name__ == "__main__":
    # For debugging purposes only
    import uvicorn
    logger.info("Starting NEXUS-AI Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
