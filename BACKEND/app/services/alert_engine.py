"""
Alert Engine

Generates alert payloads for hazard events.
Alerts are JSON structures ready for notification dispatch.

Author: NEXUS-AI Team
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from app.services.geofence_engine import (
    HazardZone,
    HazardType,
    ZoneSeverity,
    generate_flood_zone,
    generate_landslide_zone,
    register_zone,
    get_active_zones
)
from app.core.logging import get_logger

logger = get_logger("alert_engine")


class AlertType(str, Enum):
    """Types of alerts."""
    FLOOD_WARNING = "FLOOD_WARNING"
    FLOOD_WATCH = "FLOOD_WATCH"
    LANDSLIDE_ALERT = "LANDSLIDE_ALERT"
    LANDSLIDE_WATCH = "LANDSLIDE_WATCH"
    EVACUATION_ORDER = "EVACUATION_ORDER"
    ALL_CLEAR = "ALL_CLEAR"


class AlertSeverity(str, Enum):
    """Alert severity (CAP standard)."""
    EXTREME = "EXTREME"
    SEVERE = "SEVERE"
    MODERATE = "MODERATE"
    MINOR = "MINOR"


@dataclass
class Alert:
    """Represents an alert payload."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    hazard_zone: HazardZone
    headline: str
    message: str
    recommended_action: str
    issued_at: datetime
    expires_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "hazard_type": self.hazard_zone.hazard_type.value,
            "affected_zone": self.hazard_zone.polygon,
            "affected_radius_km": self.hazard_zone.radius_km,
            "center": {
                "lat": self.hazard_zone.center_lat,
                "lon": self.hazard_zone.center_lon
            },
            "headline": self.headline,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }


def get_alert_type(hazard_type: HazardType, zone_severity: ZoneSeverity) -> AlertType:
    """Determine alert type from hazard and severity."""
    if hazard_type == HazardType.FLOOD:
        if zone_severity in [ZoneSeverity.CRITICAL, ZoneSeverity.HIGH]:
            return AlertType.FLOOD_WARNING
        else:
            return AlertType.FLOOD_WATCH
    else:  # LANDSLIDE
        if zone_severity in [ZoneSeverity.CRITICAL, ZoneSeverity.HIGH]:
            return AlertType.LANDSLIDE_ALERT
        else:
            return AlertType.LANDSLIDE_WATCH


def get_alert_severity(zone_severity: ZoneSeverity) -> AlertSeverity:
    """Map zone severity to alert severity."""
    mapping = {
        ZoneSeverity.CRITICAL: AlertSeverity.EXTREME,
        ZoneSeverity.HIGH: AlertSeverity.SEVERE,
        ZoneSeverity.MEDIUM: AlertSeverity.MODERATE,
        ZoneSeverity.LOW: AlertSeverity.MINOR
    }
    return mapping.get(zone_severity, AlertSeverity.MODERATE)


def get_recommended_action(alert_type: AlertType, severity: AlertSeverity) -> str:
    """Get recommended action based on alert type and severity."""
    if severity == AlertSeverity.EXTREME:
        return "EVACUATE IMMEDIATELY to higher ground. Follow official instructions."
    elif severity == AlertSeverity.SEVERE:
        return "PREPARE TO EVACUATE. Move valuables to upper floors. Avoid low-lying areas."
    elif severity == AlertSeverity.MODERATE:
        return "STAY ALERT. Monitor official channels. Avoid unnecessary travel in affected areas."
    else:
        return "BE AWARE. Stay informed of weather conditions."


def format_flood_message(zone: HazardZone) -> str:
    """Format flood alert message."""
    pred = zone.source_prediction
    probability = pred.get("probability", 0)
    lead_time = pred.get("lead_time_hours", 12)
    station_id = pred.get("station_id", "Unknown")
    
    return (
        f"Flood risk detected near {station_id}. "
        f"Probability: {probability*100:.0f}%. "
        f"Expected within {lead_time} hours. "
        f"Affected radius: {zone.radius_km:.1f}km. "
        f"Avoid low-lying areas and waterways."
    )


def format_landslide_message(zone: HazardZone) -> str:
    """Format landslide alert message."""
    pred = zone.source_prediction
    susceptibility = pred.get("susceptibility", 0)
    
    return (
        f"Landslide susceptibility elevated in area. "
        f"Susceptibility: {susceptibility*100:.0f}%. "
        f"Affected radius: {zone.radius_km:.1f}km. "
        f"Avoid steep slopes, cuts, and unstable terrain."
    )


def generate_alert(zone: HazardZone) -> Alert:
    """
    Generate an alert from a hazard zone.
    
    Args:
        zone: HazardZone to generate alert for
    
    Returns:
        Alert object
    """
    now = datetime.utcnow()
    
    # Determine alert type and severity
    alert_type = get_alert_type(zone.hazard_type, zone.severity)
    severity = get_alert_severity(zone.severity)
    
    # Generate headline
    if zone.hazard_type == HazardType.FLOOD:
        headline = f"{alert_type.value}: Flood Risk in {zone.source_prediction.get('station_id', 'Area')}"
        message = format_flood_message(zone)
    else:
        headline = f"{alert_type.value}: Landslide Risk at ({zone.center_lat:.2f}, {zone.center_lon:.2f})"
        message = format_landslide_message(zone)
    
    # Get recommended action
    action = get_recommended_action(alert_type, severity)
    
    # Generate alert ID
    alert_id = f"ALT_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
    
    alert = Alert(
        alert_id=alert_id,
        alert_type=alert_type,
        severity=severity,
        hazard_zone=zone,
        headline=headline,
        message=message,
        recommended_action=action,
        issued_at=now,
        expires_at=zone.valid_until
    )
    
    logger.info(
        "alert_generated",
        alert_id=alert_id,
        alert_type=alert_type.value,
        severity=severity.value
    )
    
    return alert


def generate_flood_alert(
    station_id: str,
    center_lat: float,
    center_lon: float,
    probability: float,
    risk_level: str,
    lead_time_hours: int = 12
) -> Alert:
    """
    Generate a flood alert from prediction.
    
    Convenience function that creates zone and alert.
    """
    zone = generate_flood_zone(
        station_id=station_id,
        center_lat=center_lat,
        center_lon=center_lon,
        probability=probability,
        risk_level=risk_level,
        lead_time_hours=lead_time_hours
    )
    
    # Register zone
    register_zone(zone)
    
    return generate_alert(zone)


def generate_landslide_alert(
    lat: float,
    lon: float,
    susceptibility: float,
    risk_level: str
) -> Alert:
    """
    Generate a landslide alert from prediction.
    
    Convenience function that creates zone and alert.
    """
    zone = generate_landslide_zone(
        lat=lat,
        lon=lon,
        susceptibility=susceptibility,
        risk_level=risk_level
    )
    
    # Register zone
    register_zone(zone)
    
    return generate_alert(zone)


def get_active_alerts() -> List[Dict[str, Any]]:
    """Get all active alerts as dictionaries."""
    zones = get_active_zones()
    alerts = [generate_alert(zone).to_dict() for zone in zones]
    return alerts


def generate_all_clear(zone_id: str) -> Alert:
    """
    Generate an all-clear alert for a zone.
    
    Used when a hazard zone is cleared.
    """
    now = datetime.utcnow()
    
    # Create minimal zone for all-clear
    zone = HazardZone(
        zone_id=zone_id,
        hazard_type=HazardType.FLOOD,  # Default
        severity=ZoneSeverity.LOW,
        center_lat=0,
        center_lon=0,
        radius_km=0,
        polygon={"type": "Polygon", "coordinates": [[]]},
        valid_from=now,
        valid_until=now + timedelta(hours=1),
        source_prediction={}
    )
    
    alert = Alert(
        alert_id=f"CLR_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}",
        alert_type=AlertType.ALL_CLEAR,
        severity=AlertSeverity.MINOR,
        hazard_zone=zone,
        headline=f"ALL CLEAR: Hazard zone {zone_id} has been cleared",
        message="The previous hazard warning has been lifted. Normal activities may resume.",
        recommended_action="Continue to monitor official channels.",
        issued_at=now,
        expires_at=now + timedelta(hours=1)
    )
    
    logger.info("all_clear_generated", zone_id=zone_id)
    
    return alert
