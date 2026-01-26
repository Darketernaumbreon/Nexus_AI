from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import UUID

class SimulationRequest(BaseModel):
    region_id: str = Field(..., description="Target region for simulation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Simulation config parameters")

class SimulationResponse(BaseModel):
    job_id: str
    status: str
    message: str = "Job submitted successfully"

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
