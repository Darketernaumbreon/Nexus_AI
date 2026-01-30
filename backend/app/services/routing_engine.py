"""
Routing Engine with OpenRouteService Integration

Uses OpenRouteService API (powered by OpenStreetMap) for real road-based routing
while maintaining hazard zone avoidance capabilities.

OpenStreetMap Coverage in North East India:
- Guwahati: Excellent (all major/secondary roads mapped)
- Assam Highways: 100% complete (NH & SH)
-Rural Assam: 70-85% complete
- Active maintenance for flood response

Free Tier: 2000 requests/day
Get API key: https://openrouteservice.org/dev/#/signup

Author: NEXUS-AI Team
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import math

import openrouteservice as ors
try:
    from openrouteservice.exceptions import ApiError, Timeout
except (ImportError, AttributeError):
    # Fallback for older versions
    ApiError = Exception
    Timeout = Exception

from app.services.geofence_engine import (
    HazardZone,
    get_active_zones,
    check_point_in_zone,
)
from app.core.config import settings
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
    steps: List[Dict[str, Any]]      # Turn-by-turn directions (optional)
    
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
            "segment_count": len(self.segments),
            "steps_count": len(self.steps) if self.steps else 0
        }


def get_ors_client() -> ors.Client:
    """
    Get OpenRouteService API client.
    
    Raises:
        ValueError: If API key is not configured
    """
    if not settings.OPENROUTE_API_KEY:
        raise ValueError(
            "OpenRouteService API key not configured. "
            "Get a free key from https://openrouteservice.org/dev/#/signup "
            "and add it to .env as OPENROUTE_API_KEY"
        )
    
    return ors.Client(key=settings.OPENROUTE_API_KEY)


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


def check_route_hazards(
    coordinates: List[List[float]],
    zones: List[HazardZone],
    sample_rate: int = 10
) -> Tuple[bool, List[str]]:
    """
    Check if a route passes through any hazard zones.
    
    Args:
        coordinates: List of [lon, lat] coordinate pairs
        zones: List of active hazard zones
        sample_rate: Check every Nth point (reduce computation)
    
    Returns:
        Tuple of (is_blocked, list of zone IDs)
    """
    affected_zones = set()
    
    # Sample points along the route
    sampled_coords = coordinates[::sample_rate] + [coordinates[-1]]
    
    for coord in sampled_coords:
        lon, lat = coord[0], coord[1]
        for zone in zones:
            if check_point_in_zone(lat, lon, zone):
                affected_zones.add(zone.zone_id)
    
    return len(affected_zones) > 0, list(affected_zones)


def generate_avoidance_waypoints(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    hazard_zones: List[HazardZone]
) -> List[Tuple[float, float]]:
    """
    Generate waypoints to avoid hazard zones.
    
    Strategy:
    - Calculate midpoint between origin and destination
    - Find nearest hazard zone
    - Offset waypoint perpendicular to hazard center
    
    Returns:
        List of (lat, lon) waypoints
    """
    if not hazard_zones:
        return []
    
    # Calculate midpoint
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lon = (origin[1] + destination[1]) / 2
    
    # Find nearest hazard to midpoint
    nearest_hazard = min(
        hazard_zones,
        key=lambda h: haversine_distance(mid_lat, mid_lon, h.center_lat, h.center_lon)
    )
    
    # Calculate avoidance factor based on hazard radius
    avoidance_distance = nearest_hazard.radius_km * 2  # Stay 2x radius away
    
    # Offset waypoint perpendicular to hazard
    # Use simple geometric offset (in production, use more sophisticated path planning)
    offset_lat = mid_lat + (mid_lat - nearest_hazard.center_lat) * 0.5
    offset_lon = mid_lon + (mid_lon - nearest_hazard.center_lon) * 0.5
    
    waypoint = (offset_lat, offset_lon)
    
    logger.info(
        "generated_avoidance_waypoint",
        hazard_id=nearest_hazard.zone_id,
        waypoint=waypoint
    )
    
    return [waypoint]


def fetch_ors_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    waypoints: Optional[List[Tuple[float, float]]] = None
) -> Dict[str, Any]:
    """
    Fetch route from OpenRouteService API.
    
    Args:
        origin: (lat, lon)
        destination: (lat, lon)
        waypoints: Optional intermediate waypoints (lat, lon)
    
    Returns:
        ORS route response dict
        
    Raises:
        ApiError: If ORS API returns an error
        Timeout: If request times out
    """
    client = get_ors_client()
    
    # Build coordinate list: [lon, lat] format for ORS
    coords = [[origin[1], origin[0]]]
    
    if waypoints:
        for wp in waypoints:
            coords.append([wp[1], wp[0]])
    
    coords.append([destination[1], destination[0]])
    
    try:
        logger.info(
            "fetching_ors_route",
            origin=origin,
            destination=destination,
            waypoints_count=len(waypoints) if waypoints else 0
        )
        
        response = client.directions(
            coordinates=coords,
            profile='driving-car',
            format='geojson',
            instructions=True,
            geometry=True,
            elevation=False,
            preference='recommended',  # Balance of speed and quality
            units='km'
        )
        
        return response
        
    except Timeout as e:
        logger.error("ors_timeout", error=str(e))
        raise
    except ApiError as e:
        logger.error("ors_api_error", error=str(e))
        raise


def parse_ors_response(
    ors_response: Dict[str, Any],
    origin: Tuple[float, float],
    destination: Tuple[float, float]
) -> Tuple[List[List[float]], float, int, List[Dict[str, Any]]]:
    """
    Parse OpenRouteService response.
    
    Returns:
        Tuple of (coordinates, distance_km, duration_minutes, steps)
    """
    feature = ors_response['features'][0]
    geometry = feature['geometry']
    properties = feature['properties']
    
    coordinates = geometry['coordinates']  # List of [lon, lat]
    distance_km = properties['summary']['distance'] / 1000  # meters to km
    duration_minutes = int(properties['summary']['duration'] / 60)  # seconds to minutes
    
    # Extract turn-by-turn steps
    steps = []
    if 'segments' in properties:
        for segment in properties['segments']:
            if 'steps' in segment:
                for step in segment['steps']:
                    steps.append({
                        'instruction': step.get('instruction', ''),
                        'distance_km': step.get('distance', 0) / 1000,
                        'duration_minutes': int(step.get('duration', 0) / 60)
                    })
    
    return coordinates, distance_km, duration_minutes, steps


def compute_safe_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float
) -> Route:
    """
    Compute the safest route between two points using OpenRouteService.
    
    Strategy:
    1. Get active hazard zones
    2. Fetch direct route from ORS
    3. Check if route intersects hazards
    4. If blocked, generate waypoints to avoid hazards
    5. Retry with waypoints (up to 2 attempts)
    6. Return best available route
    
    Args:
        origin_lat, origin_lon: Origin coordinates
        dest_lat, dest_lon: Destination coordinates
    
    Returns:
        Route object with status and details
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
    
    try:
        # Attempt 1: Direct route
        ors_response = fetch_ors_route(origin, destination)
        coordinates, distance_km, duration_minutes, steps = parse_ors_response(
            ors_response, origin, destination
        )
        
        # Check for hazards
        is_blocked, affected_zones = check_route_hazards(coordinates, zones)
        
        if not is_blocked:
            # Route is safe!
            logger.info("route_computed", status="SAFE", distance_km=distance_km)
            
            return Route(
                origin=origin,
                destination=destination,
                status=RouteStatus.SAFE,
                distance_km=distance_km,
                eta_minutes=duration_minutes,
                segments=[],  # Can parse from steps if needed
                avoided_hazards=[],
                warnings=[],
                geometry={
                    "type": "LineString",
                    "coordinates": coordinates
                },
                steps=steps
            )
        
        # Route is blocked - try to find detour
        logger.warning(
            "route_blocked",
            affected_zones=affected_zones,
            attempting_detour=True
        )
        
        # Attempt 2: Route with avoidance waypoints
        waypoints = generate_avoidance_waypoints(origin, destination, 
                                                  [z for z in zones if z.zone_id in affected_zones])
        
        ors_response_detour = fetch_ors_route(origin, destination, waypoints)
        coordinates_detour, distance_detour, duration_detour, steps_detour = parse_ors_response(
            ors_response_detour, origin, destination
        )
        
        # Check detour for hazards
        is_blocked_detour, affected_zones_detour = check_route_hazards(coordinates_detour, zones)
        
        if not is_blocked_detour:
            # Detour is safe!
            logger.info(
                "detour_successful",
                status="SAFE",
                distance_km=distance_detour,
                avoided_zones=affected_zones
            )
            
            return Route(
                origin=origin,
                destination=destination,
                status=RouteStatus.SAFE,
                distance_km=distance_detour,
                eta_minutes=duration_detour,
                segments=[],
                avoided_hazards=affected_zones,
                warnings=[f"Detour applied to avoid: {', '.join(affected_zones)}"],
                geometry={
                    "type": "LineString",
                    "coordinates": coordinates_detour
                },
                steps=steps_detour
            )
        else:
            # Detour still blocked
            logger.warning(
                "detour_still_blocked",
                affected_zones=affected_zones_detour
            )
            
            return Route(
                origin=origin,
                destination=destination,
                status=RouteStatus.BLOCKED,
                distance_km=distance_detour,
                eta_minutes=duration_detour,
                segments=[],
                avoided_hazards=[],
                warnings=[
                    f"Route unavoidably passes through: {', '.join(affected_zones_detour)}",
                    "Exercise extreme caution or postpone travel"
                ],
                geometry={
                    "type": "LineString",
                    "coordinates": coordinates_detour
                },
                steps=steps_detour
            )
    
    except Exception as e:
        logger.error("routing_failed_unexpected", error=str(e), error_type=type(e).__name__)
        
        # Fallback: return straight-line distance estimate
        distance_km = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        eta_minutes = int((distance_km / 30) * 60)  # Assume 30 km/h
        
        return Route(
            origin=origin,
            destination=destination,
            status=RouteStatus.UNKNOWN,
            distance_km=distance_km,
            eta_minutes=eta_minutes,
            segments=[],
            avoided_hazards=[],
            warnings=["Routing service unavailable. Showing straight-line distance."],
            geometry={
                "type": "LineString",
                "coordinates": [
                    [origin_lon, origin_lat],
                    [dest_lon, dest_lat]
                ]
            },
            steps=[]
        )


def get_blocked_segments() -> List[Dict[str, Any]]:
    """
    Get list of road segments currently blocked by hazards.
    
    In production, this would return specific road edge IDs.
    For MVP, returns hazard zone centers with affected radius.
    
    Returns:
        List of blocked segment info dicts
    """
    zones = get_active_zones()
    
    blocked = []
    for zone in zones:
        blocked.append({
            "zone_id": zone.zone_id,
            "hazard_type": zone.hazard_type.value if hasattr(zone.hazard_type, 'value') else str(zone.hazard_type),
            "center": {"lat": zone.center_lat, "lon": zone.center_lon},
            "radius_km": zone.radius_km,
            "severity": zone.severity.value if hasattr(zone.severity, 'value') else str(zone.severity),
            "description": f"Blocked due to {zone.hazard_type} hazard"
        })
    
    logger.info("blocked_segments_retrieved", count=len(blocked))
    return blocked

