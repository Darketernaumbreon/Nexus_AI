"""
Routing API Endpoints

Exposes safe routing services with hazard avoidance.

Endpoints:
    - GET /routing/safe - Compute safe route between two points
    - GET /routing/blocked - Get list of blocked road segments

Author: NEXUS-AI Team
"""

from typing import Dict, Any
from fastapi import APIRouter, Query

from app.services.routing_engine import (
    compute_safe_route,
    get_blocked_segments,
    RouteStatus
)
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("routing_api")


@router.get("/safe")
def get_safe_route(
    origin_lat: float = Query(..., ge=-90, le=90, description="Origin latitude"),
    origin_lon: float = Query(..., ge=-180, le=180, description="Origin longitude"),
    dest_lat: float = Query(..., ge=-90, le=90, description="Destination latitude"),
    dest_lon: float = Query(..., ge=-180, le=180, description="Destination longitude")
) -> Dict[str, Any]:
    """
    Compute a safe route between two points, avoiding hazard zones.
    
    Returns:
        Route with status (SAFE/CAUTION/BLOCKED), distance, ETA, and geometry.
    """
    logger.info(
        "safe_route_request",
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon
    )
    
    route = compute_safe_route(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon
    )
    
    return {
        "success": True,
        "route": route.to_dict()
    }


@router.get("/blocked")
def get_blocked_road_segments() -> Dict[str, Any]:
    """
    Get list of road segments currently blocked by hazards.
    
    In production, this would return specific road edge IDs.
    For MVP, returns hazard zone centers with affected radius.
    """
    logger.info("blocked_segments_request")
    
    segments = get_blocked_segments()
    
    return {
        "count": len(segments),
        "blocked_segments": segments
    }


@router.get("/check")
def check_route_safety(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lon: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lon: float = Query(..., ge=-180, le=180)
) -> Dict[str, Any]:
    """
    Quick check if a route is safe (without full route computation).
    """
    logger.info("route_safety_check")
    
    route = compute_safe_route(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon
    )
    
    return {
        "is_safe": route.status == RouteStatus.SAFE,
        "status": route.status.value,
        "warnings": route.warnings,
        "avoided_hazards": route.avoided_hazards
    }
