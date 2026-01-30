from fastapi import APIRouter, Response, status
from sqlalchemy import text
import structlog

from app.db.session import engine
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.get("/live", status_code=200)
async def liveness_probe():
    """
    Checks if the process is running.
    """
    return {"status": "alive"}

@router.get("/ready", status_code=200)
async def readiness_probe(response: Response):
    """
    Deep check: Verifies DB and Redis connectivity.
    """
    checks = {
        "database": False,
        "redis": False
    }
    
    # 1. Check Database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error("Readiness check failed: Database unreachable", error=str(e))
        
    # 2. Check Redis (using arq settings)
    try:
        from arq import create_pool
        pool = await create_pool(settings.REDIS_SETTINGS)
        await pool.ping()
        await pool.close()
        checks["redis"] = True
    except Exception as e:
        logger.error("Readiness check failed: Redis unreachable", error=str(e))

    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "checks": checks}
