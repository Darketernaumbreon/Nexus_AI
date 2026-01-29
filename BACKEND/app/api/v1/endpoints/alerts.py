"""
Alert API Endpoints

Exposes alert generation and management services.

Endpoints:
    - POST /alerts/generate - Generate alert from prediction
    - GET /alerts/check - Check if location is in alert zone
    - GET /alerts/active - List all active alerts

Author: NEXUS-AI Team
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.services.alert_engine import (
    generate_flood_alert,
    generate_landslide_alert,
    get_active_alerts,
    Alert
)
from app.services.geofence_engine import (
    get_active_zones,
    get_zones_containing_point,
    get_nearby_zones,
    expire_zones
)
from app.services.flood_inference import predict_flood
from app.services.landslide_inference import predict_landslide
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("alerts_api")


class FloodAlertRequest(BaseModel):
    """Request body for flood alert generation."""
    station_id: str = Field(..., description="CWC gauge station ID")
    center_lat: float = Field(..., ge=-90, le=90)
    center_lon: float = Field(..., ge=-180, le=180)
    probability: Optional[float] = Field(None, ge=0, le=1, description="Override probability")
    risk_level: Optional[str] = Field(None, description="Override risk level")
    lead_time_hours: int = Field(12, ge=1, le=72)


class LandslideAlertRequest(BaseModel):
    """Request body for landslide alert generation."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    susceptibility: Optional[float] = Field(None, ge=0, le=1)
    risk_level: Optional[str] = Field(None)


@router.post("/generate/flood")
def generate_flood_alert_endpoint(
    request: Request,
    body: FloodAlertRequest
) -> Dict[str, Any]:
    """
    Generate a flood alert from prediction or manual input.
    
    If probability/risk_level not provided, will fetch from prediction API.
    """
    logger.info("generate_flood_alert_request", station_id=body.station_id)
    
    probability = body.probability
    risk_level = body.risk_level
    
    # If not provided, get from prediction
    if probability is None or risk_level is None:
        try:
            prediction = predict_flood(request, body.station_id)
            probability = probability or prediction.get("probability", 0.5)
            risk_level = risk_level or prediction.get("risk_level", "MEDIUM")
        except Exception as e:
            logger.warning("prediction_fallback", error=str(e))
            probability = probability or 0.5
            risk_level = risk_level or "MEDIUM"
    
    try:
        alert = generate_flood_alert(
            station_id=body.station_id,
            center_lat=body.center_lat,
            center_lon=body.center_lon,
            probability=probability,
            risk_level=risk_level,
            lead_time_hours=body.lead_time_hours
        )
        
        return {
            "success": True,
            "alert": alert.to_dict()
        }
    except Exception as e:
        logger.error("flood_alert_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/landslide")
def generate_landslide_alert_endpoint(
    request: Request,
    body: LandslideAlertRequest
) -> Dict[str, Any]:
    """
    Generate a landslide alert from prediction or manual input.
    """
    logger.info("generate_landslide_alert_request", lat=body.lat, lon=body.lon)
    
    susceptibility = body.susceptibility
    risk_level = body.risk_level
    
    # If not provided, get from prediction
    if susceptibility is None or risk_level is None:
        try:
            prediction = predict_landslide(request, body.lat, body.lon)
            susceptibility = susceptibility or prediction.get("susceptibility", 0.5)
            risk_level = risk_level or prediction.get("risk_level", "MEDIUM")
        except Exception as e:
            logger.warning("prediction_fallback", error=str(e))
            susceptibility = susceptibility or 0.5
            risk_level = risk_level or "MEDIUM"
    
    try:
        alert = generate_landslide_alert(
            lat=body.lat,
            lon=body.lon,
            susceptibility=susceptibility,
            risk_level=risk_level
        )
        
        return {
            "success": True,
            "alert": alert.to_dict()
        }
    except Exception as e:
        logger.error("landslide_alert_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check")
def check_location_alerts(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    buffer_km: float = Query(5.0, ge=0.1, le=50)
) -> Dict[str, Any]:
    """
    Check if a location is in or near any active alert zones.
    
    Returns zones containing the point and nearby zones within buffer.
    """
    logger.info("check_location_alerts", lat=lat, lon=lon)
    
    # Expire old zones first
    expire_zones()
    
    zones = get_active_zones()
    
    # Check zones containing point
    containing = get_zones_containing_point(lat, lon, zones)
    
    # Check nearby zones
    nearby = get_nearby_zones(lat, lon, zones, buffer_km)
    
    # Determine overall status
    if containing:
        status = "IN_DANGER_ZONE"
        max_severity = max(z.severity.value for z in containing)
    elif nearby:
        status = "NEAR_DANGER_ZONE"
        max_severity = nearby[0][0].severity.value if nearby else "NONE"
    else:
        status = "CLEAR"
        max_severity = "NONE"
    
    return {
        "location": {"lat": lat, "lon": lon},
        "status": status,
        "max_severity": max_severity,
        "zones_inside": [z.to_dict() for z in containing],
        "zones_nearby": [
            {"zone": z.to_dict(), "distance_km": round(d, 2)}
            for z, d in nearby if z not in containing
        ][:5]  # Limit to 5 nearest
    }


@router.get("/active")
def get_active_alerts_endpoint() -> Dict[str, Any]:
    """
    Get all currently active alerts.
    """
    logger.info("get_active_alerts_request")
    
    # Expire old zones first
    expire_zones()
    
    alerts = get_active_alerts()
    
    return {
        "count": len(alerts),
        "alerts": alerts
    }


@router.get("/zones")
def get_active_zones_endpoint() -> Dict[str, Any]:
    """
    Get all currently active hazard zones.
    """
    logger.info("get_active_zones_request")
    
    # Expire old zones first
    expired_count = expire_zones()
    
    zones = get_active_zones()
    
    return {
        "count": len(zones),
        "expired": expired_count,
        "zones": [z.to_dict() for z in zones]
    }


@router.get("/imd-rainfall")
def get_imd_rainfall_endpoint(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get authoritative IMD rainfall data (Gridded).
    """
    from app.modules.environmental.tasks.imd_etl import fetch_imd_rainfall
    from datetime import date, timedelta
    
    # Default to last 3 days if not specified
    if not end_date:
        end = date.today()
    else:
        end = date.fromisoformat(end_date)
        
    if not start_date:
        start = end - timedelta(days=2) 
    else:
        start = date.fromisoformat(start_date)
        
    try:
        data = fetch_imd_rainfall(start, end)
        return {
            "source": "IMD (Indian Meteorological Department)",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        logger.error(f"Failed to fetch IMD data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch IMD data")
