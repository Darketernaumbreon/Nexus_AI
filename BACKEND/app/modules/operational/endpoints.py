from fastapi import APIRouter, HTTPException, Depends, status
from arq import create_pool
from arq.connections import ArqRedis
from arq.jobs import Job
from typing import Any

from app.core.config import settings
from app.modules.operational.schemas import SimulationRequest, SimulationResponse, JobStatusResponse
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Dependency to get Redis Pool
# In a full app, this might be stored in app.state.arq_pool via lifespan
async def get_arq_pool() -> ArqRedis:
    # Creating a new pool per request is inefficient; 
    # for this skeletal implementation it suffices, but ideally use app.state
    # We will assume a singleton pattern or app state integration in main.py usually
    return await create_pool(settings.REDIS_SETTINGS)

@router.post("/simulate", response_model=SimulationResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_simulation(
    request: SimulationRequest,
    # pool: ArqRedis = Depends(get_arq_pool) # Simplified dependency
):
    """
    Triggers an asynchronous simulation (ML/Operational Model).
    Returns 202 Accepted with job_id.
    """
    try:
        pool = await create_pool(settings.REDIS_SETTINGS)
        # Enqueue the job 'run_simulation' defined in worker.py
        job = await pool.enqueue_job(
            "run_simulation", 
            simulation_id=f"sim_{request.region_id}", 
            parameters=request.parameters
        )
        await pool.close()
        
        if not job:
            raise HTTPException(status_code=500, detail="Failed to enqueue job")

        return SimulationResponse(
            job_id=job.job_id,
            status="queued"
        )
    except Exception as e:
        logger.error(f"Failed to enqueue simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Polls the status of a simulation job.
    """
    try:
        pool = await create_pool(settings.REDIS_SETTINGS)
        job = Job(job_id, pool)
        
        if not job:
            await pool.close()
            raise HTTPException(status_code=404, detail="Job not found")

        # Check status
        status = await job.status()
        result = None
        if status == "complete":
            result = await job.result()
        
        await pool.close()
        
        return JobStatusResponse(
            job_id=job_id,
            status=str(status),
            result=result
        )

    except Exception as e:
        logger.error(f"Failed to fetch job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
