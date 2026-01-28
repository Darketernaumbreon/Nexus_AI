"""
Prediction API Endpoints

Exposes flood and landslide prediction services.
Models are loaded once at startup (see app/core/lifespan.py).

Endpoints:
    - GET /predict/flood?station_id=XYZ
    - GET /predict/landslide?lat=26.2&lon=91.7
    - GET /predict/risk (legacy, combined)

Author: NEXUS-AI Team
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request

from app.services.flood_inference import predict_flood
from app.services.landslide_inference import predict_landslide
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("predictions_api")


@router.get("/flood")
def get_flood_prediction(
    request: Request,
    station_id: str = Query(..., description="CWC gauge station ID", min_length=1)
) -> Dict[str, Any]:
    """
    Predict flood risk for a CWC gauge station.
    
    Args:
        station_id: CWC gauge station ID (e.g., "BRAHMAPUTRA_GWH01")
    
    Returns:
        Flood risk prediction with:
        - probability: Flood probability [0, 1]
        - risk_level: HIGH / MEDIUM / LOW / NEGLIGIBLE
        - lead_time_hours: Estimated hours before event
        - top_drivers: Top-5 SHAP feature explanations
        - confidence: Prediction confidence level
    
    Latency: < 300ms (cached)
    """
    logger.info("flood_endpoint_called", station_id=station_id)
    
    try:
        result = predict_flood(request, station_id)
        return result
    except Exception as e:
        logger.error("flood_prediction_failed", error=str(e), station_id=station_id)
        raise HTTPException(
            status_code=500,
            detail=f"Flood prediction failed: {str(e)}"
        )


@router.get("/landslide")
def get_landslide_prediction(
    request: Request,
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180)
) -> Dict[str, Any]:
    """
    Predict landslide susceptibility for a location.
    
    Args:
        lat: Latitude of the location
        lon: Longitude of the location
    
    Returns:
        Landslide susceptibility prediction with:
        - susceptibility: Landslide probability [0, 1]
        - risk_level: HIGH / MEDIUM / LOW / NEGLIGIBLE
        - top_drivers: Top-5 SHAP feature explanations
        - confidence: Prediction confidence level
    
    Latency: < 300ms (cached)
    """
    logger.info("landslide_endpoint_called", lat=lat, lon=lon)
    
    try:
        result = predict_landslide(request, lat, lon)
        return result
    except Exception as e:
        logger.error("landslide_prediction_failed", error=str(e), lat=lat, lon=lon)
        raise HTTPException(
            status_code=500,
            detail=f"Landslide prediction failed: {str(e)}"
        )


@router.get("/risk")
def get_combined_risk(
    request: Request,
    lat: float = Query(..., description="Latitude of the location", ge=-90, le=90),
    lon: float = Query(..., description="Longitude of the location", ge=-180, le=180),
    station_id: str = Query(None, description="Optional: CWC gauge station ID for flood risk")
) -> Dict[str, Any]:
    """
    Get combined hazard risk for a location.
    
    This endpoint provides both flood (if station_id provided) and 
    landslide risks for route planning.
    
    Args:
        lat: Latitude
        lon: Longitude
        station_id: Optional CWC gauge station ID
    
    Returns:
        Combined risk assessment
    """
    logger.info("combined_risk_endpoint_called", lat=lat, lon=lon, station_id=station_id)
    
    result = {
        "location": {"lat": lat, "lon": lon},
        "hazards": {}
    }
    
    # Get landslide risk (always available for any location)
    try:
        landslide_result = predict_landslide(request, lat, lon)
        result["hazards"]["landslide"] = {
            "susceptibility": landslide_result.get("susceptibility"),
            "risk_level": landslide_result.get("risk_level"),
            "top_drivers": landslide_result.get("top_drivers", [])[:3]
        }
    except Exception as e:
        result["hazards"]["landslide"] = {"error": str(e)}
    
    # Get flood risk if station provided
    if station_id:
        try:
            flood_result = predict_flood(request, station_id)
            result["hazards"]["flood"] = {
                "probability": flood_result.get("probability"),
                "risk_level": flood_result.get("risk_level"),
                "lead_time_hours": flood_result.get("lead_time_hours"),
                "top_drivers": flood_result.get("top_drivers", [])[:3]
            }
        except Exception as e:
            result["hazards"]["flood"] = {"error": str(e)}
    
    # Compute overall risk (highest of available)
    risk_levels = []
    if "risk_level" in result["hazards"].get("landslide", {}):
        risk_levels.append(result["hazards"]["landslide"]["risk_level"])
    if "risk_level" in result["hazards"].get("flood", {}):
        risk_levels.append(result["hazards"]["flood"]["risk_level"])
    
    # Risk priority: HIGH > MEDIUM > LOW > NEGLIGIBLE
    priority = {"HIGH": 4, "MEDIUM": 3, "LOW": 2, "NEGLIGIBLE": 1}
    if risk_levels:
        result["overall_risk"] = max(risk_levels, key=lambda x: priority.get(x, 0))
    else:
        result["overall_risk"] = "UNKNOWN"
    
    return result


@router.get("/health")
def prediction_health_check(request: Request) -> Dict[str, Any]:
    """
    Check if prediction models are loaded and ready.
    """
    ml_models = getattr(request.app.state, 'ml_models', None)
    
    if ml_models is None:
        return {
            "status": "unhealthy",
            "message": "Models not initialized"
        }
    
    flood_ready = ml_models.get("flood") is not None
    landslide_ready = ml_models.get("landslide") is not None
    
    return {
        "status": "healthy" if (flood_ready and landslide_ready) else "degraded",
        "flood_model": "ready" if flood_ready else "unavailable",
        "landslide_model": "ready" if landslide_ready else "unavailable"
    }
