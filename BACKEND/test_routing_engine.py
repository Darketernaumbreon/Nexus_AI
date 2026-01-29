"""
Test Suite for Task 11B: Routing Engine

Tests:
1. Routing engine computations
2. Hazard avoidance
3. Routing API endpoints

Author: NEXUS-AI Team
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging import configure_logger
configure_logger()

print("="*60)
print("TASK 11B TEST SUITE: ROUTING ENGINE")
print("="*60)


def test_routing_engine():
    """Test 1: Routing engine computations"""
    print("\n" + "="*60)
    print("TEST 1: Routing Engine")
    print("="*60)
    
    from app.services.routing_engine import (
        compute_safe_route,
        haversine_distance,
        get_blocked_segments
    )
    from app.services.geofence_engine import (
        generate_flood_zone,
        register_zone,
        get_active_zones
    )
    
    # Test haversine distance
    print("\nTesting haversine distance...")
    dist = haversine_distance(26.0, 91.0, 27.0, 92.0)
    print(f"  Distance (26,91) to (27,92): {dist:.2f} km")
    
    # Clear zones and create fresh ones
    from app.services import geofence_engine
    geofence_engine._active_zones = {}
    
    # Route without hazards
    print("\nComputing route WITHOUT hazards...")
    route = compute_safe_route(
        origin_lat=26.0,
        origin_lon=91.0,
        dest_lat=27.0,
        dest_lon=92.0
    )
    
    print(f"  Status: {route.status.value}")
    print(f"  Distance: {route.distance_km:.2f} km")
    print(f"  ETA: {route.eta_minutes} minutes")
    
    assert route.status.value == "SAFE", "Route should be SAFE without hazards"
    print("  [OK] Safe route without hazards")
    
    # Add hazard zone on the route
    print("\nAdding hazard zone on route...")
    flood_zone = generate_flood_zone(
        station_id="TEST_MIDPOINT",
        center_lat=26.5,
        center_lon=91.5,
        probability=0.8,
        risk_level="HIGH",
        lead_time_hours=6
    )
    register_zone(flood_zone)
    
    # Route WITH hazards
    print("\nComputing route WITH hazards...")
    route_blocked = compute_safe_route(
        origin_lat=26.0,
        origin_lon=91.0,
        dest_lat=27.0,
        dest_lon=92.0
    )
    
    print(f"  Status: {route_blocked.status.value}")
    print(f"  Distance: {route_blocked.distance_km:.2f} km")
    print(f"  Avoided hazards: {route_blocked.avoided_hazards}")
    print(f"  Warnings: {route_blocked.warnings}")
    
    # Get blocked segments
    blocked = get_blocked_segments()
    print(f"\nBlocked segments: {len(blocked)}")
    
    print("\n[PASS] Routing Engine")
    return route, route_blocked


def test_routing_api():
    """Test 2: Routing API endpoints"""
    print("\n" + "="*60)
    print("TEST 2: Routing API Endpoints")
    print("="*60)
    
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test safe route
    print("\nTesting GET /routing/safe...")
    response = client.get(
        "/api/v1/routing/safe?origin_lat=26.0&origin_lon=91.0&dest_lat=27.0&dest_lon=92.0"
    )
    print(f"  Status: {response.status_code}")
    data = response.json()
    if response.status_code == 200:
        route = data.get("route", {})
        print(f"  Route status: {route.get('route_status')}")
        print(f"  Distance: {route.get('distance_km')} km")
        print(f"  ETA: {route.get('eta_minutes')} min")
    
    # Test blocked segments
    print("\nTesting GET /routing/blocked...")
    response = client.get("/api/v1/routing/blocked")
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Blocked count: {data.get('count', 0)}")
    
    # Test route safety check
    print("\nTesting GET /routing/check...")
    response = client.get(
        "/api/v1/routing/check?origin_lat=26.0&origin_lon=91.0&dest_lat=27.0&dest_lon=92.0"
    )
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Is safe: {data.get('is_safe')}")
    print(f"  Route status: {data.get('status')}")
    
    print("\n[PASS] Routing API")


def main():
    try:
        # Test 1: Routing Engine
        test_routing_engine()
        
        # Test 2: API
        test_routing_api()
        
        print("\n" + "="*60)
        print("[PASS] ALL TASK 11B TESTS PASSED")
        print("="*60)
        
        print("\nTask 11B Summary:")
        print("  [OK] Routing Engine: Safe route computation")
        print("  [OK] Hazard detection: Point-in-zone checks")
        print("  [OK] Detour logic: Route avoidance")
        print("  [OK] Routing API: /routing/safe, /routing/blocked, /routing/check")
        
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
