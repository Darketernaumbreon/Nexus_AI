"""
Geofence Engine

Generates and manages hazard zone polygons for flood and landslide events.
Used for alert targeting and route blocking.

Author: NEXUS-AI Team
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import math

from app.core.logging import get_logger

logger = get_logger("geofence_engine")


class HazardType(str, Enum):
    """Types of hazards."""
    FLOOD = "FLOOD"
    LANDSLIDE = "LANDSLIDE"


class ZoneSeverity(str, Enum):
    """Zone severity levels."""
    CRITICAL = "CRITICAL"  # Immediate danger
    HIGH = "HIGH"          # High risk
    MEDIUM = "MEDIUM"      # Moderate risk
    LOW = "LOW"            # Low risk


@dataclass
class HazardZone:
    """Represents a hazard zone polygon."""
    zone_id: str
    hazard_type: HazardType
    severity: ZoneSeverity
    center_lat: float
    center_lon: float
    radius_km: float
    polygon: Dict[str, Any]  # GeoJSON Polygon
    valid_from: datetime
    valid_until: datetime
    source_prediction: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "hazard_type": self.hazard_type.value,
            "severity": self.severity.value,
            "center": {"lat": self.center_lat, "lon": self.center_lon},
            "radius_km": self.radius_km,
            "polygon": self.polygon,
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat()
        }


def get_affected_radius_km(risk_level: str) -> float:
    """
    Get affected radius based on risk level.
    
    Scaling:
        - HIGH: 5km (evacuation zone)
        - MEDIUM: 3km (warning zone)
        - LOW: 1km (watch zone)
        - NEGLIGIBLE: 0.5km (awareness zone)
    """
    radius_map = {
        "HIGH": 5.0,
        "MEDIUM": 3.0,
        "LOW": 1.0,
        "NEGLIGIBLE": 0.5
    }
    return radius_map.get(risk_level.upper(), 1.0)


def create_circle_polygon(
    center_lat: float,
    center_lon: float,
    radius_km: float,
    num_points: int = 32
) -> Dict[str, Any]:
    """
    Create a circular GeoJSON polygon around a center point.
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_km: Radius in kilometers
        num_points: Number of polygon vertices
    
    Returns:
        GeoJSON Polygon
    """
    # Convert radius to degrees (approximate)
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 * cos(lat) km
    lat_offset = radius_km / 111.0
    lon_offset = radius_km / (111.0 * math.cos(math.radians(center_lat)))
    
    coordinates = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        lat = center_lat + lat_offset * math.sin(angle)
        lon = center_lon + lon_offset * math.cos(angle)
        coordinates.append([lon, lat])
    
    # Close the polygon
    coordinates.append(coordinates[0])
    
    return {
        "type": "Polygon",
        "coordinates": [coordinates]
    }


def generate_flood_zone(
    station_id: str,
    center_lat: float,
    center_lon: float,
    probability: float,
    risk_level: str,
    lead_time_hours: int = 12
) -> HazardZone:
    """
    Generate a flood hazard zone from prediction.
    
    Args:
        station_id: CWC gauge station ID
        center_lat: Station latitude
        center_lon: Station longitude
        probability: Flood probability
        risk_level: Risk level (HIGH/MEDIUM/LOW)
        lead_time_hours: Hours until predicted event
    
    Returns:
        HazardZone object
    """
    now = datetime.utcnow()
    
    # Get radius based on risk
    radius_km = get_affected_radius_km(risk_level)
    
    # Map risk to severity
    severity_map = {
        "HIGH": ZoneSeverity.CRITICAL,
        "MEDIUM": ZoneSeverity.HIGH,
        "LOW": ZoneSeverity.MEDIUM,
        "NEGLIGIBLE": ZoneSeverity.LOW
    }
    severity = severity_map.get(risk_level.upper(), ZoneSeverity.MEDIUM)
    
    # Create polygon
    polygon = create_circle_polygon(center_lat, center_lon, radius_km)
    
    # Generate zone ID
    zone_id = f"FLD_{station_id}_{now.strftime('%Y%m%d%H%M')}"
    
    zone = HazardZone(
        zone_id=zone_id,
        hazard_type=HazardType.FLOOD,
        severity=severity,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=radius_km,
        polygon=polygon,
        valid_from=now,
        valid_until=now + timedelta(hours=lead_time_hours + 6),  # Buffer
        source_prediction={
            "station_id": station_id,
            "probability": probability,
            "risk_level": risk_level,
            "lead_time_hours": lead_time_hours
        }
    )
    
    logger.info(
        "flood_zone_generated",
        zone_id=zone_id,
        severity=severity.value,
        radius_km=radius_km
    )
    
    return zone


def generate_landslide_zone(
    lat: float,
    lon: float,
    susceptibility: float,
    risk_level: str
) -> HazardZone:
    """
    Generate a landslide hazard zone from prediction.
    
    Args:
        lat: Latitude of prediction point
        lon: Longitude of prediction point
        susceptibility: Landslide susceptibility
        risk_level: Risk level (HIGH/MEDIUM/LOW)
    
    Returns:
        HazardZone object
    """
    now = datetime.utcnow()
    
    # Landslide zones are typically smaller than flood zones
    base_radius = get_affected_radius_km(risk_level)
    radius_km = base_radius * 0.6  # 60% of flood radius
    
    # Map risk to severity
    severity_map = {
        "HIGH": ZoneSeverity.CRITICAL,
        "MEDIUM": ZoneSeverity.HIGH,
        "LOW": ZoneSeverity.MEDIUM,
        "NEGLIGIBLE": ZoneSeverity.LOW
    }
    severity = severity_map.get(risk_level.upper(), ZoneSeverity.MEDIUM)
    
    # Create polygon
    polygon = create_circle_polygon(lat, lon, radius_km)
    
    # Generate zone ID
    zone_id = f"LND_{int(lat*100)}_{int(lon*100)}_{now.strftime('%Y%m%d%H%M')}"
    
    zone = HazardZone(
        zone_id=zone_id,
        hazard_type=HazardType.LANDSLIDE,
        severity=severity,
        center_lat=lat,
        center_lon=lon,
        radius_km=radius_km,
        polygon=polygon,
        valid_from=now,
        valid_until=now + timedelta(hours=24),  # Landslide zones valid 24h
        source_prediction={
            "lat": lat,
            "lon": lon,
            "susceptibility": susceptibility,
            "risk_level": risk_level
        }
    )
    
    logger.info(
        "landslide_zone_generated",
        zone_id=zone_id,
        severity=severity.value,
        radius_km=radius_km
    )
    
    return zone


def check_point_in_zone(
    lat: float,
    lon: float,
    zone: HazardZone
) -> bool:
    """
    Check if a point is inside a hazard zone.
    
    Uses simple distance check (faster than full polygon check).
    
    Args:
        lat: Point latitude
        lon: Point longitude
        zone: HazardZone to check
    
    Returns:
        True if point is inside zone
    """
    # Haversine distance (simplified)
    lat_diff = lat - zone.center_lat
    lon_diff = lon - zone.center_lon
    
    # Approximate distance in km
    lat_km = lat_diff * 111.0
    lon_km = lon_diff * 111.0 * math.cos(math.radians(zone.center_lat))
    distance_km = math.sqrt(lat_km**2 + lon_km**2)
    
    return distance_km <= zone.radius_km


def get_zones_containing_point(
    lat: float,
    lon: float,
    zones: List[HazardZone]
) -> List[HazardZone]:
    """
    Find all hazard zones that contain a given point.
    
    Args:
        lat: Point latitude
        lon: Point longitude
        zones: List of hazard zones to check
    
    Returns:
        List of zones containing the point
    """
    containing_zones = []
    for zone in zones:
        if check_point_in_zone(lat, lon, zone):
            containing_zones.append(zone)
    
    return containing_zones


def get_nearby_zones(
    lat: float,
    lon: float,
    zones: List[HazardZone],
    buffer_km: float = 5.0
) -> List[Tuple[HazardZone, float]]:
    """
    Find hazard zones near a point (within buffer distance).
    
    Args:
        lat: Point latitude
        lon: Point longitude
        zones: List of hazard zones to check
        buffer_km: Buffer distance in km
    
    Returns:
        List of (zone, distance_km) tuples, sorted by distance
    """
    nearby = []
    
    for zone in zones:
        # Calculate distance to zone center
        lat_diff = lat - zone.center_lat
        lon_diff = lon - zone.center_lon
        lat_km = lat_diff * 111.0
        lon_km = lon_diff * 111.0 * math.cos(math.radians(zone.center_lat))
        distance_km = math.sqrt(lat_km**2 + lon_km**2)
        
        # Check if within buffer of zone edge
        if distance_km <= zone.radius_km + buffer_km:
            nearby.append((zone, distance_km))
    
    # Sort by distance
    nearby.sort(key=lambda x: x[1])
    
    return nearby


# In-memory zone store (for demo; use DB in production)
_active_zones: Dict[str, HazardZone] = {}


def register_zone(zone: HazardZone) -> None:
    """Register a zone as active."""
    _active_zones[zone.zone_id] = zone
    logger.info("zone_registered", zone_id=zone.zone_id)


def get_active_zones() -> List[HazardZone]:
    """Get all currently active zones."""
    now = datetime.utcnow()
    active = [z for z in _active_zones.values() if z.valid_until > now]
    return active


def expire_zones() -> int:
    """Remove expired zones. Returns count of expired zones."""
    now = datetime.utcnow()
    expired = [zid for zid, z in _active_zones.items() if z.valid_until <= now]
    for zid in expired:
        del _active_zones[zid]
    if expired:
        logger.info("zones_expired", count=len(expired))
    return len(expired)
