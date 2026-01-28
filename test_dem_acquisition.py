"""
Test script for DEM acquisition module.
Tests OpenTopography API integration and caching.
"""

from pathlib import Path
from app.modules.geospatial.clients.opentopography import fetch_dem
from app.modules.geospatial.utils.raster_validation import validate_dem

def test_dem_fetch():
    """Test DEM fetching for small Assam region."""
    print("=" * 60)
    print("Testing DEM Acquisition Module")
    print("=" * 60)
    
    # Small test area in Assam, India (Brahmaputra region)
    min_lat, min_lon = 26.0, 91.0
    max_lat, max_lon = 26.2, 91.2
    
    print(f"\n1. Fetching DEM for bbox: ({min_lat}, {min_lon}) to ({max_lat}, {max_lon})")
    print(f"   Dataset: COP30")
    print(f"   This will download ~5-10 MB...")
    
    try:
        dem_path = fetch_dem(min_lat, min_lon, max_lat, max_lon, dataset="COP30")
        
        print(f"\n[OK] DEM fetched successfully!")
        print(f"   Path: {dem_path}")
        print(f"   Exists: {dem_path.exists()}")
        
        if dem_path.exists():
            size_mb = dem_path.stat().st_size / 1024 / 1024
            print(f"   Size: {size_mb:.2f} MB")
        
        # Validate DEM
        print(f"\n2. Validating DEM...")
        metadata = validate_dem(dem_path)
        
        print(f"\n   Validation Results:")
        print(f"   - Valid: {metadata['valid']}")
        print(f"   - CRS: {metadata['crs']}")
        print(f"   - Resolution: {metadata['resolution']}m")
        print(f"   - NoData: {metadata['nodata']}")
        print(f"   - Elevation range: {metadata['min_elev']}m to {metadata['max_elev']}m")
        print(f"   - Void percentage: {metadata['void_pct']}%")
        
        if metadata['warnings']:
            print(f"\n   Warnings:")
            for warning in metadata['warnings']:
                print(f"   - {warning}")
        
        # Test caching
        print(f"\n3. Testing cache (re-fetching same bbox)...")
        dem_path2 = fetch_dem(min_lat, min_lon, max_lat, max_lon, dataset="COP30")
        
        if dem_path == dem_path2:
            print(f"   [OK] Cache working! Same file returned: {dem_path.name}")
        else:
            print(f"   [ERROR] Cache failed - different files returned")
        
        print(f"\n{'=' * 60}")
        print("[OK] All tests passed!")
        print(f"{'=' * 60}")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dem_fetch()
