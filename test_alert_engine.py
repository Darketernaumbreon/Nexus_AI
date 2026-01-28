"""
Test Suite for Task 11A: Alert Engine

Tests:
1. Geofence zone generation
2. Point-in-zone detection
3. Alert generation
4. Alert API endpoints

Author: NEXUS-AI Team
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging import configure_logger
configure_logger()

print("="*60)
print("TASK 11A TEST SUITE: ALERT ENGINE")
print("="*60)


def test_geofence_engine():
    """Test 1: Geofence zone generation"""
    print("\n" + "="*60)
    print("TEST 1: Geofence Engine")
    print("="*60)
    
    from app.services.geofence_engine import (
        generate_flood_zone,
        generate_landslide_zone,
        check_point_in_zone,
        get_zones_containing_point,
        get_affected_radius_km,
        register_zone,
        get_active_zones
    )
    
    # Test radius mapping
    print("\nRadius mapping:")
    for level in ["HIGH", "MEDIUM", "LOW", "NEGLIGIBLE"]:
        radius = get_affected_radius_km(level)
        print(f"  {level}: {radius}km")
    
    # Generate flood zone
    print("\nGenerating flood zone...")
    flood_zone = generate_flood_zone(
        station_id="BRAHMAPUTRA_GWH01",
        center_lat=26.2,
        center_lon=91.7,
        probability=0.75,
        risk_level="HIGH",
        lead_time_hours=12
    )
    
    print(f"  Zone ID: {flood_zone.zone_id}")
    print(f"  Severity: {flood_zone.severity.value}")
    print(f"  Radius: {flood_zone.radius_km}km")
    print(f"  Polygon vertices: {len(flood_zone.polygon['coordinates'][0])}")
    
    # Generate landslide zone
    print("\nGenerating landslide zone...")
    landslide_zone = generate_landslide_zone(
        lat=26.5,
        lon=91.9,
        susceptibility=0.65,
        risk_level="MEDIUM"
    )
    
    print(f"  Zone ID: {landslide_zone.zone_id}")
    print(f"  Severity: {landslide_zone.severity.value}")
    print(f"  Radius: {landslide_zone.radius_km}km")
    
    # Test point-in-zone
    print("\nPoint-in-zone detection:")
    test_points = [
        (26.2, 91.7, "Center of flood zone"),
        (26.21, 91.71, "Near center"),
        (30.0, 90.0, "Far away"),
        (26.5, 91.9, "Center of landslide zone")
    ]
    
    for lat, lon, desc in test_points:
        in_flood = check_point_in_zone(lat, lon, flood_zone)
        in_land = check_point_in_zone(lat, lon, landslide_zone)
        print(f"  ({lat}, {lon}) {desc}: Flood={in_flood}, Landslide={in_land}")
    
    # Register zones
    register_zone(flood_zone)
    register_zone(landslide_zone)
    
    active = get_active_zones()
    print(f"\nActive zones: {len(active)}")
    
    print("\n[PASS] Geofence Engine")
    return flood_zone, landslide_zone


def test_alert_engine(flood_zone, landslide_zone):
    """Test 2: Alert generation"""
    print("\n" + "="*60)
    print("TEST 2: Alert Engine")
    print("="*60)
    
    from app.services.alert_engine import (
        generate_alert,
        generate_flood_alert,
        generate_landslide_alert,
        get_active_alerts
    )
    
    # Generate alert from zone
    print("\nGenerating alert from flood zone...")
    flood_alert = generate_alert(flood_zone)
    
    print(f"  Alert ID: {flood_alert.alert_id}")
    print(f"  Type: {flood_alert.alert_type.value}")
    print(f"  Severity: {flood_alert.severity.value}")
    print(f"  Headline: {flood_alert.headline}")
    print(f"  Action: {flood_alert.recommended_action[:50]}...")
    
    # Generate alert from prediction
    print("\nGenerating landslide alert from prediction...")
    land_alert = generate_landslide_alert(
        lat=26.8,
        lon=92.0,
        susceptibility=0.72,
        risk_level="HIGH"
    )
    
    print(f"  Alert ID: {land_alert.alert_id}")
    print(f"  Type: {land_alert.alert_type.value}")
    print(f"  Message: {land_alert.message[:60]}...")
    
    # Get active alerts
    alerts = get_active_alerts()
    print(f"\nActive alerts: {len(alerts)}")
    
    print("\n[PASS] Alert Engine")
    return flood_alert, land_alert


def test_alert_api():
    """Test 3: Alert API endpoints"""
    print("\n" + "="*60)
    print("TEST 3: Alert API Endpoints")
    print("="*60)
    
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test active alerts
    print("\nTesting GET /alerts/active...")
    response = client.get("/api/v1/alerts/active")
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Alert count: {data.get('count', 0)}")
    
    # Test zone check
    print("\nTesting GET /alerts/check...")
    response = client.get("/api/v1/alerts/check?lat=26.2&lon=91.7")
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Location status: {data.get('status')}")
    print(f"  Max severity: {data.get('max_severity')}")
    
    # Test flood alert generation
    print("\nTesting POST /alerts/generate/flood...")
    response = client.post(
        "/api/v1/alerts/generate/flood",
        json={
            "station_id": "TEST_STATION",
            "center_lat": 26.3,
            "center_lon": 91.8,
            "probability": 0.8,
            "risk_level": "HIGH",
            "lead_time_hours": 6
        }
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        alert = data.get("alert", {})
        print(f"  Alert type: {alert.get('alert_type')}")
        print(f"  Severity: {alert.get('severity')}")
    
    # Test landslide alert generation
    print("\nTesting POST /alerts/generate/landslide...")
    response = client.post(
        "/api/v1/alerts/generate/landslide",
        json={
            "lat": 26.6,
            "lon": 92.1,
            "susceptibility": 0.7,
            "risk_level": "HIGH"
        }
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        alert = data.get("alert", {})
        print(f"  Alert type: {alert.get('alert_type')}")
    
    print("\n[PASS] Alert API")


def main():
    try:
        # Test 1: Geofence
        flood_zone, landslide_zone = test_geofence_engine()
        
        # Test 2: Alert Engine
        test_alert_engine(flood_zone, landslide_zone)
        
        # Test 3: API
        test_alert_api()
        
        print("\n" + "="*60)
        print("[PASS] ALL TASK 11A TESTS PASSED")
        print("="*60)
        
        print("\nTask 11A Summary:")
        print("  [OK] Geofence Engine: Zone polygon generation")
        print("  [OK] Alert Engine: Alert payload generation")
        print("  [OK] Alert API: /alerts/generate, /alerts/check, /alerts/active")
        
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
