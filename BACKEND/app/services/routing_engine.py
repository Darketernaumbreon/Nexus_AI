"""
Routing Engine

Computes safe routes avoiding hazard zones.
Uses mock routing for MVP (pgRouting integration for production).

Latency Budget:
    - Hazard check: <= 20ms
    - Route computation: <= 200ms
    - Total: <= 250ms

Author: NEXUS-AI Team
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.modules.geospatial.models import NavEdge

from app.services.geofence_engine import (
    HazardZone,
    get_active_zones,
    check_point_in_zone,
    get_nearby_zones
)
from app.core.logging import get_logger

logger = get_logger("routing_engine")


class RouteStatus(str, Enum):
    """Route status codes."""
    SAFE = "SAFE"                    # Route avoids all hazards
    CAUTION = "CAUTION"              # Route passes near hazards
    BLOCKED = "BLOCKED"              # All routes blocked by hazards
    PARTIAL = "PARTIAL"              # Some segments blocked
    UNKNOWN = "UNKNOWN"              # Cannot determine


@dataclass
class RouteSegment:
    """A segment of a route."""
    start: Tuple[float, float]       # (lat, lon)
    end: Tuple[float, float]         # (lat, lon)
    distance_km: float
    is_blocked: bool
    hazard_zones: List[str]          # Zone IDs affecting this segment


@dataclass
class Route:
    """Represents a computed route."""
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    status: RouteStatus
    distance_km: float
    eta_minutes: int
    segments: List[RouteSegment]
    avoided_hazards: List[str]
    warnings: List[str]
    geometry: Dict[str, Any]         # GeoJSON LineString
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin": {"lat": self.origin[0], "lon": self.origin[1]},
            "destination": {"lat": self.destination[0], "lon": self.destination[1]},
            "route_status": self.status.value,
            "distance_km": round(self.distance_km, 2),
            "eta_minutes": self.eta_minutes,
            "avoided_hazards": self.avoided_hazards,
            "warnings": self.warnings,
            "geometry": self.geometry,
            "segment_count": len(self.segments)
        }


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points (in km).
    """
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def interpolate_points(
    start: Tuple[float, float],
    end: Tuple[float, float],
    num_points: int = 10
) -> List[Tuple[float, float]]:
    """
    Interpolate points between start and end.
    """
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        lat = start[0] + t * (end[0] - start[0])
        lon = start[1] + t * (end[1] - start[1])
        points.append((lat, lon))
    return points


def check_segment_hazards(
    start: Tuple[float, float],
    end: Tuple[float, float],
    zones: List[HazardZone],
    sample_points: int = 10
) -> Tuple[bool, List[str]]:
    """
    Check if a route segment passes through any hazard zones.
    
    Returns:
        Tuple of (is_blocked, list of zone IDs)
    """
    points = interpolate_points(start, end, sample_points)
    affected_zones = set()
    
    for point in points:
        for zone in zones:
            if check_point_in_zone(point[0], point[1], zone):
                affected_zones.add(zone.zone_id)
    
    return len(affected_zones) > 0, list(affected_zones)


async def compute_direct_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    zones: List[HazardZone]
) -> Route:
    """
    Compute a direct route and check for hazards.
    
    Tries Google Maps API first, falls back to simple calculation.
    """
    # 1. Try Google Maps API for accurate distance/duration/polyline
    from app.modules.geospatial.clients.google_maps import GoogleMapsRoutingClient
    try:
        gmaps = GoogleMapsRoutingClient()
        gmaps_result = await gmaps.get_route(
            {"lat": origin[0], "lon": origin[1]}, 
            {"lat": destination[0], "lon": destination[1]}
        )
        
        if gmaps_result:
            # Use Google Maps data
            # Distance comes in meters
            distance_km = float(gmaps_result.get("distanceMeters", 0)) / 1000.0
            
            # Duration comes as "123s" string usually, need parsing if strictly needed, 
            # but routing engine uses simplified minutes integer.
            duration_str = gmaps_result.get("duration", "0s")
            duration_seconds = int(duration_str.rstrip('s'))
            eta_minutes = duration_seconds // 60
            
            # Use the detailed polyline from Google
            # Note: We'd need to decode this polyline for hazard checking points
            # For MVP, we stick to linear interpolation for hazard checking 
            # OR we decode the polyline.
            # Let's assume linear hazard check for now to match interface.
        else:
             raise ValueError("Google Maps returned no route")
             
    except Exception as e:
        # Fallback to Haversine
        # logger.warning(f"Google Maps Routing failed: {e}. Using fallback.")
        distance_km = haversine_distance(
            origin[0], origin[1],
            destination[0], destination[1]
        )
        eta_minutes = int((distance_km / 30) * 60)
    
    # Check for hazards along the route (using linear interpolation for now)
    # In V2, we should decode the google polyline
    is_blocked, affected_zones = check_segment_hazards(origin, destination, zones)
    
    # Create segment
    segment = RouteSegment(
        start=origin,
        end=destination,
        distance_km=distance_km,
        is_blocked=is_blocked,
        hazard_zones=affected_zones
    )
    
    # Determine status
    if is_blocked:
        status = RouteStatus.BLOCKED
        warnings = [f"Route blocked by: {', '.join(affected_zones)}"]
    elif affected_zones:
        status = RouteStatus.CAUTION
        warnings = [f"Route passes near: {', '.join(affected_zones)}"]
    else:
        status = RouteStatus.SAFE
        warnings = []
    
    # Create GeoJSON geometry
    geometry = {
        "type": "LineString",
        "coordinates": [
            [origin[1], origin[0]],
            [destination[1], destination[0]]
        ]
    }
    
    return Route(
        origin=origin,
        destination=destination,
        status=status,
        distance_km=distance_km,
        eta_minutes=eta_minutes,
        segments=[segment],
        avoided_hazards=[],
        warnings=warnings,
        geometry=geometry
    )


async def compute_detour_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    zones: List[HazardZone],
    detour_factor: float = 1.3
) -> Route:
    """
    Compute a detour route that avoids hazard zones.
    
    Simple heuristic: offset the midpoint away from hazard centers.
    In production, use pgRouting with blocked edges.
    """
    # Find hazard centers
    hazard_centers = [(z.center_lat, z.center_lon, z.zone_id) for z in zones]
    
    if not hazard_centers:
        return await compute_direct_route(origin, destination, zones)
    
    # Calculate midpoint
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lon = (origin[1] + destination[1]) / 2
    
    # Find nearest hazard
    nearest_hazard = min(
        hazard_centers,
        key=lambda h: haversine_distance(mid_lat, mid_lon, h[0], h[1])
    )
    
    # Offset midpoint away from hazard
    offset_lat = mid_lat + (mid_lat - nearest_hazard[0]) * 0.3
    offset_lon = mid_lon + (mid_lon - nearest_hazard[1]) * 0.3
    
    waypoint = (offset_lat, offset_lon)
    
    # Check segments
    seg1_blocked, seg1_zones = check_segment_hazards(origin, waypoint, zones)
    seg2_blocked, seg2_zones = check_segment_hazards(waypoint, destination, zones)
    
    # Calculate distances
    dist1 = haversine_distance(origin[0], origin[1], waypoint[0], waypoint[1])
    dist2 = haversine_distance(waypoint[0], waypoint[1], destination[0], destination[1])
    total_distance = dist1 + dist2
    
    # ETA
    eta_minutes = int((total_distance / 30) * 60)
    
    # Segments
    segments = [
        RouteSegment(
            start=origin,
            end=waypoint,
            distance_km=dist1,
            is_blocked=seg1_blocked,
            hazard_zones=seg1_zones
        ),
        RouteSegment(
            start=waypoint,
            end=destination,
            distance_km=dist2,
            is_blocked=seg2_blocked,
            hazard_zones=seg2_zones
        )
    ]
    
    # Status
    all_zones = set(seg1_zones + seg2_zones)
    is_blocked = seg1_blocked or seg2_blocked
    
    if is_blocked:
        status = RouteStatus.PARTIAL
        warnings = [f"Detour still affected by: {', '.join(all_zones)}"]
    else:
        status = RouteStatus.SAFE
        warnings = []
    
    # Geometry
    geometry = {
        "type": "LineString",
        "coordinates": [
            [origin[1], origin[0]],
            [waypoint[1], waypoint[0]],
            [destination[1], destination[0]]
        ]
    }
    
    return Route(
        origin=origin,
        destination=destination,
        status=status,
        distance_km=total_distance,
        eta_minutes=eta_minutes,
        segments=segments,
        avoided_hazards=[nearest_hazard[2]],
        warnings=warnings,
        geometry=geometry
    )


async def compute_safe_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float
) -> Route:
    """
    Compute the safest route between two points.
    
    Tries direct route first, then detour if blocked.
    
    Args:
        origin_lat, origin_lon: Origin coordinates
        dest_lat, dest_lon: Destination coordinates
    
    Returns:
        Route object
    """
    origin = (origin_lat, origin_lon)
    destination = (dest_lat, dest_lon)
    
    logger.info(
        "computing_safe_route",
        origin=origin,
        destination=destination
    )
    
    # Get active hazard zones
    zones = get_active_zones()
    
    if not zones:
        # No hazards, return direct route
        route = await compute_direct_route(origin, destination, [])
        logger.info("route_computed", status="SAFE", hazards=0)
        return route
    
    # Try direct route
    direct_route = await compute_direct_route(origin, destination, zones)
    
    if direct_route.status == RouteStatus.SAFE:
        logger.info("route_computed", status="SAFE", hazards=len(zones))
        return direct_route
    
    # Try detour
    detour_route = await compute_detour_route(origin, destination, zones)
    
    logger.info(
        "route_computed",
        status=detour_route.status.value,
        avoided=detour_route.avoided_hazards
    )
    
    return detour_route


def get_blocked_segments(zones: Optional[List[HazardZone]] = None) -> List[Dict[str, Any]]:
    """
    Get list of blocked road segments (simplified).
    
    In production, this would query road network edges
    that intersect with hazard zones.
    """
    if zones is None:
        zones = get_active_zones()
    
    blocked = []
    for zone in zones:
        blocked.append({
            "zone_id": zone.zone_id,
            "hazard_type": zone.hazard_type.value,
            "severity": zone.severity.value,
            "center": {"lat": zone.center_lat, "lon": zone.center_lon},
            "radius_km": zone.radius_km,
            "description": f"Road segments within {zone.radius_km}km of {zone.zone_id} may be blocked"
        })
    
    return blocked


async def get_full_network(db: AsyncSession) -> Dict[str, Any]:
    """
    Get the full road network for visualization.
    Returns list of edges formatted as 'routes' for the dashboard.
    """
    # Use ST_AsText to get WKT string which is easier to parse quickly for MVP
    # or ST_AsGeoJSON. Let's use ST_AsGeoJSON for direct usage.
    stmt = select(NavEdge, func.ST_AsGeoJSON(NavEdge.geom).label('geojson'))
    result = await db.execute(stmt)
    rows = result.all()
    
    routes = []
    
    import json
    
    for row in rows:
        edge = row[0]
        geojson_str = row[1]
        geometry = json.loads(geojson_str)
        
        # Extract coordinates from LineString [[lon, lat], [lon, lat]]
        coordinates = geometry.get('coordinates', [])
        
        # Format segments for frontend
        route_data = {
            "id": str(edge.id),
            "name": edge.name or f"Route {edge.id}",
            "total_length_km": edge.base_cost,
            "average_risk_score": int((hash(str(edge.id)) % 100)), # Simulated Risk for Demo
            "coordinates": coordinates,
            "segments": [
                {
                    "id": str(edge.id),
                    "is_blocked": (hash(str(edge.id)) % 20) == 0, # 5% chance of blockage
                    "risk_score": int((hash(str(edge.id)) % 100)),
                    "name": edge.name or "Segment",
                    "length_km": edge.base_cost,
                    "surface_type": edge.surface_type
                }
            ]
        }
        routes.append(route_data)
        
    return {
        "routes": routes,
        "lastUpdated": datetime.utcnow().isoformat(),
        # Approximate bounds for North East (Assam) or dynamic
        "bounds": { "north": 28.0, "south": 24.0, "east": 96.0, "west": 89.0 } 
    }

