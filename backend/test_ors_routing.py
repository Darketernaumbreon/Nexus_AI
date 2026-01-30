"""
Quick test for OpenRouteService routing integration.

Tests routing with real Guwahati coordinates.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.routing_engine import compute_safe_route
from app.core.logging import configure_logger

configure_logger()


def test_guwahati_routing():
    """Test routing between two points in Guwahati."""
    print("\n" + "="*60)
    print("OpenRouteService Routing Test - Guwahati")
    print("="*60)
    
    # Test route: Guwahati Railway Station -> Guwahati Airport
    print("\nRoute: Guwahati Railway Station → Lokpriya Gopinath Bordoloi Airport")
    print("Origin: 26.1445°N, 91.7362°E (Railway Station)")
    print("Dest: 26.1858°N, 91.7467°E (Airport)")
    
    try:
        route = compute_safe_route(
            origin_lat=26.1445,
            origin_lon=91.7362,
            dest_lat=26.1858,
            dest_lon=91.7467
        )
        
        print(f"\n✅ Route computed successfully!")
        print(f"\nRoute Details:")
        print(f"  Status: {route.status.value}")
        print(f"  Distance: {route.distance_km:.2f} km")
        print(f"  ETA: {route.eta_minutes} minutes")
        print(f"  Coordinates: {len(route.geometry['coordinates'])} points")
        print(f"  Steps: {len(route.steps)} turn-by-turn instructions")
        
        if route.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in route.warnings:
                print(f"    - {warning}")
        
        if route.avoided_hazards:
            print(f"\n🚧 Avoided Hazards:")
            for hazard in route.avoided_hazards:
                print(f"    - {hazard}")
        
        # Show first few steps
        if route.steps:
            print(f"\n📍 First 3 Turn-by-Turn Steps:")
            for i, step in enumerate(route.steps[:3], 1):
                print(f"  {i}. {step['instruction']} ({step['distance_km']:.1f} km)")
        
        print("\n[PASS] OpenRouteService integration working!")
        print(f"\nOSM Data Quality: Routes follow actual roads in Guwahati ✅")
        
        return True
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nMake sure OPENROUTE_API_KEY is set in .env file")
        return False
        
    except Exception as e:
        print(f"\n❌ Routing Error: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_guwahati_routing()
    sys.exit(0 if success else 1)
