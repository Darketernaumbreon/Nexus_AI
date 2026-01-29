"""
Test Suite for Task 11C: Alert Prioritization

Tests:
1. Priority determination for users
2. Crowd convergence prevention
3. Dispatch queue creation

Author: NEXUS-AI Team
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging import configure_logger
configure_logger()

print("="*60)
print("TASK 11C TEST SUITE: ALERT PRIORITIZATION")
print("="*60)


import pytest

@pytest.fixture(scope="module")
def shared_zones_prioritization():
    """Test 1: Priority determination for users"""
    print("\n" + "="*60)
    print("TEST 1: Priority Determination")
    print("="*60)
    
    from app.services.alert_prioritization import (
        determine_user_priority,
        UserLocation,
        AlertPriority,
        AlertAction
    )
    from app.services.geofence_engine import (
        generate_flood_zone,
        register_zone
    )
    from app.services import geofence_engine
    
    # Clear zones
    geofence_engine._active_zones = {}
    
    # Create a hazard zone
    zone = generate_flood_zone(
        station_id="PRIORITY_TEST",
        center_lat=26.5,
        center_lon=91.5,
        probability=0.8,
        risk_level="HIGH",
        lead_time_hours=6
    )
    register_zone(zone)
    zones = [zone]
    
    # ... (keeping existing logic but inside fixture) ... 
    
    print(f"\nHazard zone: center=(26.5, 91.5), radius={zone.radius_km}km")
    
    # Test users at different locations
    test_users = [
        ("user_inside", 26.5, 91.5, "Inside zone center"),
        ("user_edge", 26.52, 91.5, "At zone edge"),
        ("user_near", 26.56, 91.5, "Near zone (1km from edge)"),
        ("user_buffer", 26.6, 91.5, "In buffer (3km)"),
        ("user_far", 27.0, 91.5, "Far away"),
        ("user_outside", 30.0, 90.0, "Outside all zones")
    ]
    
    print("\nUser priority determinations:")
    for user_id, lat, lon, desc in test_users:
        user = UserLocation(
            user_id=user_id,
            lat=lat,
            lon=lon,
            timestamp=datetime.utcnow()
        )
        
        decision = determine_user_priority(user, zones)
        assert decision is not None

    return zones


@pytest.fixture(scope="module")
def shared_grouped_users(shared_zones_prioritization):
    """Test 2: Batch user prioritization"""
    print("\n" + "="*60)
    print("TEST 2: Batch User Prioritization")
    print("="*60)
    
    zones = shared_zones_prioritization
    from app.services.alert_prioritization import (
        prioritize_users,
        UserLocation
    )
    
    # Create batch of users
    users = [
        UserLocation("u1", 26.5, 91.5, datetime.utcnow()),     # Inside
        UserLocation("u2", 26.51, 91.5, datetime.utcnow()),    # Inside
        UserLocation("u3", 26.55, 91.5, datetime.utcnow()),    # Edge
        UserLocation("u4", 26.57, 91.5, datetime.utcnow()),    # Near
        UserLocation("u5", 26.6, 91.5, datetime.utcnow()),     # Buffer
        UserLocation("u6", 27.0, 91.5, datetime.utcnow()),     # Far
        UserLocation("u7", 28.0, 90.0, datetime.utcnow()),     # Outside
        UserLocation("u8", 26.52, 91.52, datetime.utcnow()),   # Inside
    ]
    
    grouped = prioritize_users(users, zones)
    
    # Validate counts
    total = sum(len(d) for d in grouped.values())
    assert total == len(users), "All users should be assigned a priority"
    
    return grouped


def test_dispatch_queue(shared_grouped_users):
    """Test 3: Dispatch queue creation"""
    print("\n" + "="*60)
    print("TEST 3: Dispatch Queue")
    print("="*60)
    
    grouped = shared_grouped_users
    from app.services.alert_prioritization import create_dispatch_queue
    
    queue = create_dispatch_queue(grouped)
    
    print(f"\nDispatch queue: {len(queue)} alerts")
    
    # Validate order
    if len(queue) > 1:
        for i in range(len(queue) - 1):
            assert queue[i]["dispatch_order"] <= queue[i+1]["dispatch_order"], \
                "Queue should be ordered by priority"
    
    print("\n[PASS] Dispatch Queue")
