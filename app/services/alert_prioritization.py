"""
Alert Prioritization Service

Targets alerts based on user proximity to danger zones.
Prevents crowd convergence and prioritizes evacuation orders.

Priority Tiers:
    P0: Inside danger zone → EVACUATION
    P1: Within buffer (1-5km) → STAY_AWAY
    P2: On approach route → DIVERSION
    --: Outside all zones → NO_ALERT

Author: NEXUS-AI Team
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.services.geofence_engine import (
    HazardZone,
    get_active_zones,
    check_point_in_zone,
    get_nearby_zones,
    get_zones_containing_point
)
from app.services.alert_engine import Alert, generate_alert, AlertType, AlertSeverity
from app.core.logging import get_logger

logger = get_logger("alert_prioritization")


class AlertPriority(str, Enum):
    """Alert priority levels."""
    P0_CRITICAL = "P0"      # Immediate evacuation
    P1_HIGH = "P1"          # High urgency (stay away)
    P2_MEDIUM = "P2"        # Medium urgency (diversion)
    P3_LOW = "P3"           # Low urgency (awareness)
    NONE = "NONE"           # No alert needed


class AlertAction(str, Enum):
    """Recommended actions for alert recipients."""
    EVACUATE = "EVACUATE"
    STAY_AWAY = "STAY_AWAY"
    DIVERT = "DIVERT"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"


@dataclass
class UserLocation:
    """Represents a user's location."""
    user_id: str
    lat: float
    lon: float
    timestamp: datetime
    heading: Optional[float] = None  # Direction of travel (degrees)


@dataclass
class AlertDecision:
    """Decision on whether/how to alert a user."""
    user_id: str
    should_alert: bool
    priority: AlertPriority
    action: AlertAction
    zones: List[str]           # Relevant zone IDs
    message: str
    reason: str


def determine_user_priority(
    user: UserLocation,
    zones: List[HazardZone],
    buffer_km: float = 5.0
) -> AlertDecision:
    """
    Determine alert priority for a user based on their location.
    
    Args:
        user: User location
        zones: Active hazard zones
        buffer_km: Buffer distance for "nearby" classification
    
    Returns:
        AlertDecision with priority and action
    """
    # Check if user is inside any zone
    containing_zones = get_zones_containing_point(user.lat, user.lon, zones)
    
    if containing_zones:
        # P0: Inside danger zone - EVACUATE
        zone_ids = [z.zone_id for z in containing_zones]
        max_severity = max(z.severity.value for z in containing_zones)
        
        return AlertDecision(
            user_id=user.user_id,
            should_alert=True,
            priority=AlertPriority.P0_CRITICAL,
            action=AlertAction.EVACUATE,
            zones=zone_ids,
            message=f"EMERGENCY: You are inside a {max_severity} hazard zone. Evacuate immediately.",
            reason="User location inside hazard zone"
        )
    
    # Check nearby zones
    nearby = get_nearby_zones(user.lat, user.lon, zones, buffer_km)
    
    if nearby:
        nearest_zone, distance = nearby[0]
        
        if distance <= nearest_zone.radius_km + 1.0:
            # P1: Very close to zone edge - STAY AWAY
            return AlertDecision(
                user_id=user.user_id,
                should_alert=True,
                priority=AlertPriority.P1_HIGH,
                action=AlertAction.STAY_AWAY,
                zones=[z.zone_id for z, d in nearby[:3]],
                message=f"WARNING: Hazard zone {distance:.1f}km away. Stay away from the area.",
                reason=f"User within 1km of zone edge"
            )
        elif distance <= nearest_zone.radius_km + 3.0:
            # P2: Moderate distance - DIVERT if approaching
            return AlertDecision(
                user_id=user.user_id,
                should_alert=True,
                priority=AlertPriority.P2_MEDIUM,
                action=AlertAction.DIVERT,
                zones=[z.zone_id for z, d in nearby[:2]],
                message=f"CAUTION: Hazard zone {distance:.1f}km away. Consider alternate routes.",
                reason=f"User within 3km of zone edge"
            )
        else:
            # P3: Far but aware - MONITOR
            return AlertDecision(
                user_id=user.user_id,
                should_alert=True,
                priority=AlertPriority.P3_LOW,
                action=AlertAction.MONITOR,
                zones=[nearest_zone.zone_id],
                message=f"ADVISORY: Hazard activity in region. Monitor official updates.",
                reason=f"User within buffer zone ({distance:.1f}km)"
            )
    
    # No alert needed
    return AlertDecision(
        user_id=user.user_id,
        should_alert=False,
        priority=AlertPriority.NONE,
        action=AlertAction.NO_ACTION,
        zones=[],
        message="",
        reason="User outside all hazard zones and buffers"
    )


def prioritize_users(
    users: List[UserLocation],
    zones: Optional[List[HazardZone]] = None
) -> Dict[str, List[AlertDecision]]:
    """
    Prioritize alerts for a list of users.
    
    Returns decisions grouped by priority.
    
    Args:
        users: List of user locations
        zones: Optional list of zones (defaults to active zones)
    
    Returns:
        Dict with priority keys and list of AlertDecision values
    """
    if zones is None:
        zones = get_active_zones()
    
    if not zones:
        logger.info("no_active_zones_for_prioritization")
        return {p.value: [] for p in AlertPriority}
    
    # Process all users
    decisions = [determine_user_priority(user, zones) for user in users]
    
    # Group by priority
    grouped = {p.value: [] for p in AlertPriority}
    for decision in decisions:
        grouped[decision.priority.value].append(decision)
    
    # Log summary
    logger.info(
        "prioritization_complete",
        total_users=len(users),
        p0=len(grouped["P0"]),
        p1=len(grouped["P1"]),
        p2=len(grouped["P2"]),
        p3=len(grouped["P3"]),
        none=len(grouped["NONE"])
    )
    
    return grouped


def prevent_crowd_convergence(
    decisions: List[AlertDecision],
    zones: List[HazardZone],
    max_evacuees_per_route: int = 100
) -> List[AlertDecision]:
    """
    Adjust alert messages to prevent crowd convergence.
    
    If too many users are directed to the same evacuation route,
    some will be rerouted to prevent traffic jams.
    
    Args:
        decisions: List of alert decisions
        zones: Active hazard zones
        max_evacuees_per_route: Max users per evacuation route
    
    Returns:
        Adjusted list of decisions
    """
    # For MVP, just add a warning if too many P0 alerts
    p0_count = sum(1 for d in decisions if d.priority == AlertPriority.P0_CRITICAL)
    
    if p0_count > max_evacuees_per_route:
        logger.warning(
            "crowd_convergence_risk",
            evacuees=p0_count,
            limit=max_evacuees_per_route
        )
        
        # Split evacuees into waves (simplified)
        wave = 1
        for decision in decisions:
            if decision.priority == AlertPriority.P0_CRITICAL:
                decision.message += f" [Evacuation Wave {wave}]"
                wave = (wave % 3) + 1  # Rotate through 3 waves
    
    return decisions


def create_dispatch_queue(
    decisions: Dict[str, List[AlertDecision]]
) -> List[Dict[str, Any]]:
    """
    Create a priority queue for alert dispatch.
    
    Higher priority alerts are dispatched first.
    
    Returns:
        Ordered list of alert dispatch items
    """
    queue = []
    
    # P0 first
    for decision in decisions.get("P0", []):
        queue.append({
            "user_id": decision.user_id,
            "priority": "P0",
            "action": decision.action.value,
            "message": decision.message,
            "zones": decision.zones,
            "dispatch_order": 1
        })
    
    # P1 second
    for decision in decisions.get("P1", []):
        queue.append({
            "user_id": decision.user_id,
            "priority": "P1",
            "action": decision.action.value,
            "message": decision.message,
            "zones": decision.zones,
            "dispatch_order": 2
        })
    
    # P2 third
    for decision in decisions.get("P2", []):
        queue.append({
            "user_id": decision.user_id,
            "priority": "P2",
            "action": decision.action.value,
            "message": decision.message,
            "zones": decision.zones,
            "dispatch_order": 3
        })
    
    # P3 last (informational only)
    for decision in decisions.get("P3", []):
        queue.append({
            "user_id": decision.user_id,
            "priority": "P3",
            "action": decision.action.value,
            "message": decision.message,
            "zones": decision.zones,
            "dispatch_order": 4
        })
    
    logger.info("dispatch_queue_created", total_alerts=len(queue))
    
    return queue
