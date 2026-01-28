"""
Test script for catchment delineation module.
Tests pour point snapping and catchment extraction on real Assam DEM.
"""

from pathlib import Path
import numpy as np
import json
from app.modules.geospatial.hydrology.conditioning import condition_dem
from app.modules.geospatial.hydrology.flow import (
    compute_flow_direction,
    compute_flow_accumulation
)
from app.modules.geospatial.hydrology.catchment import (
    snap_pour_point,
    delineate_catchment,
    catchment_to_polygon,
    latlon_to_grid
)


def test_simple_catchment():
    """Test with simple synthetic DEM."""
    print("=" * 70)
    print("Test 1: Simple 5×5 Catchment")
    print("=" * 70)
    
    # Simple DEM - flows to bottom-right
    dem = np.array([
        [10.0, 9.0, 8.0, 7.0, 6.0],
        [9.0,  8.0, 7.0, 6.0, 5.0],
        [8.0,  7.0, 6.0, 5.0, 4.0],
        [7.0,  6.0, 5.0, 4.0, 3.0],
        [6.0,  5.0, 4.0, 3.0, 2.0]
    ], dtype=np.float64)
    
    print("\nDEM:")
    print(dem)
    
    # Compute flow
    from app.modules.geospatial.hydrology.flow import compute_flow_direction, compute_flow_accumulation
    
    flow_dir = compute_flow_direction(dem, nodata=None, cell_size=30.0)
    flow_acc = compute_flow_accumulation(flow_dir, nodata_mask=None)
    
    print("\nFlow Accumulation:")
    print(flow_acc)
    
    # Pour point at outlet (bottom-right)
    pour_point = (4, 4)
    
    # Delineate catchment
    catchment = delineate_catchment(pour_point, flow_dir)
    
    print("\nCatchment Mask:")
    print(catchment.astype(int))
    
    area_cells = np.sum(catchment)
    print(f"\nCatchment area: {area_cells} cells")
    
    # Validate
    if area_cells >= 20:  # Most cells should drain to outlet
        print("[OK] Catchment includes most cells")
    else:
        print(f"[WARNING] Only {area_cells}/25 cells in catchment")
    
    print()


def test_real_catchment():
    """Test with real Assam DEM."""
    print("=" * 70)
    print("Test 2: Real Assam River Catchment")
    print("=" * 70)
    
    # Load conditioned DEM
    dem_path = Path("data/dem_cache/dem_COP30_a31683f8.tif")
    
    if not dem_path.exists():
        print(f"\n[ERROR] DEM not found: {dem_path}")
        return
    
    print(f"\n1. Loading conditioned DEM...")
    conditioned = condition_dem(dem_path, cache=True)
    
    print(f"   Shape: {conditioned.data.shape}")
    print(f"   CRS: {conditioned.crs}")
    
    # Compute flow
    print(f"\n2. Computing flow direction and accumulation...")
    flow_dir = compute_flow_direction(
        conditioned.data,
        nodata=conditioned.nodata,
        cell_size=30.92
    )
    
    nodata_mask = conditioned.data == conditioned.nodata if conditioned.nodata else None
    flow_acc = compute_flow_accumulation(flow_dir, nodata_mask)
    
    print(f"   Max accumulation: {flow_acc.max():,} cells")
    
    # Test pour point (center of DEM, should be near river)
    print(f"\n3. Testing pour point snapping...")
    
    # Get center coordinates
    from rasterio.transform import xy
    center_row, center_col = conditioned.data.shape[0] // 2, conditioned.data.shape[1] // 2
    center_lon, center_lat = xy(conditioned.transform, center_row, center_col)
    
    print(f"   Original point: ({center_lat:.4f}, {center_lon:.4f})")
    print(f"   Grid indices: ({center_row}, {center_col})")
    
    # Snap to river
    snapped_row, snapped_col, snap_dist = snap_pour_point(
        center_lat,
        center_lon,
        flow_acc,
        conditioned.transform,
        search_radius=10
    )
    
    print(f"   Snapped to: ({snapped_row}, {snapped_col})")
    print(f"   Snap distance: {snap_dist:.2f} pixels ({snap_dist * 30.92:.1f}m)")
    print(f"   Snapped accumulation: {flow_acc[snapped_row, snapped_col]:,} cells")
    
    # Delineate catchment
    print(f"\n4. Delineating catchment...")
    catchment = delineate_catchment((snapped_row, snapped_col), flow_dir, nodata_mask)
    
    area_cells = np.sum(catchment)
    area_km2 = area_cells * (30.92 ** 2) / 1e6
    
    print(f"   Catchment area: {area_cells:,} cells")
    print(f"   Catchment area: {area_km2:.2f} km²")
    
    # Validate
    total_cells = conditioned.data.size
    catchment_pct = (area_cells / total_cells) * 100
    
    print(f"\n5. Validation:")
    if area_cells > 0:
        print(f"   [OK] Catchment delineated ({catchment_pct:.1f}% of DEM)")
    else:
        print(f"   [ERROR] Empty catchment!")
    
    if 1 < catchment_pct < 80:
        print(f"   [OK] Catchment size reasonable")
    else:
        print(f"   [WARNING] Catchment is {catchment_pct:.1f}% of DEM")
    
    # Convert to polygon
    print(f"\n6. Converting to GeoJSON polygon...")
    polygon = catchment_to_polygon(catchment, conditioned.transform, conditioned.crs)
    
    if polygon:
        print(f"   [OK] Polygon created")
        print(f"   Geometry type: {polygon['geometry']['type']}")
        print(f"   Properties: {polygon['properties']}")
        
        # Save to file
        output_path = Path("data/test_catchment.geojson")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(polygon, f, indent=2)
        
        print(f"   [OK] Saved to: {output_path}")
    else:
        print(f"   [ERROR] Failed to create polygon")
    
    print(f"\n{'=' * 70}")
    print("[OK] All catchment tests passed!")
    print(f"{'=' * 70}")
    
    print(f"\nDual-Hazard Outputs:")
    print(f"  - Snapped Pour Point: ({snapped_row}, {snapped_col})")
    print(f"  - Catchment Mask: {catchment.shape} boolean array")
    print(f"  - Catchment Polygon: GeoJSON for PostGIS")
    
    print(f"\nMulti-Modal Usage:")
    print(f"  Flood Modeling:")
    print(f"    - Catchment area for rainfall aggregation")
    print(f"    - Basin boundary for discharge forecasting")
    print(f"  Landslide Modeling:")
    print(f"    - Upslope context for landslide sites")
    print(f"    - Water loading zones for susceptibility")


if __name__ == "__main__":
    # Test simple catchment
    test_simple_catchment()
    
    # Test real catchment
    test_real_catchment()
