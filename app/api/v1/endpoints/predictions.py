
from fastapi import APIRouter, HTTPException, Query
from app.schemas.prediction import PredictionResponse, PredictionData, RiskDriver
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/risk", response_model=PredictionResponse)
def predict_risk(
    lat: float = Query(..., description="Latitude of the location", ge=-90, le=90),
    lon: float = Query(..., description="Longitude of the location", ge=-180, le=180)
):
    """
    Stub endpoint to predict disaster risk for a given location.
    Currently returns mock data.
    """
    logger.info(f"Received prediction request for lat={lat}, lon={lon}")
    
    # Mock Logic: In a real scenario, this would call the ML service
    # For MVP skeleton, we return the deterministic mock structure as required
    
    mock_data = PredictionData(
        risk_score=0.72,
        risk_level="high",
        confidence=85.0,
        drivers=[
            RiskDriver(feature="rainfall_24h", impact=0.45),
            RiskDriver(feature="slope", impact=0.27)
        ],
        recommended_action="avoid"
    )
    
    return PredictionResponse(success=True, data=mock_data)
