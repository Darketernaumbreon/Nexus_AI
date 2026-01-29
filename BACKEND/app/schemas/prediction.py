
from typing import List, Literal
from pydantic import BaseModel

class RiskDriver(BaseModel):
    feature: str
    impact: float

class PredictionData(BaseModel):
    risk_score: float
    risk_level: Literal["low", "medium", "high"]
    confidence: float
    drivers: List[RiskDriver]
    recommended_action: Literal["proceed", "avoid", "reroute"]

class PredictionResponse(BaseModel):
    success: bool
    data: PredictionData
