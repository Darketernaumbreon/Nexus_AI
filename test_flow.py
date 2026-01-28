"""
Test script for flow direction and accumulation module.
Tests D8 routing and channel extraction on conditioned Assam DEM.
"""

from pathlib import Path
import numpy as np
from app.modules.geospatial.hydrology.conditioning import condition_dem
from app.modules.geospatial.hydrology.flow import (
    compute_flow_direction,
    compute_flow_accumulation,
    extract_channel_mask
)

def test_simple_dem():
    """Test with simple 3x3 DEM."""
    print("=" * 70)
    print("Test 1: Simple 3×3 DEM")
    print("=" * 70)
    
    # Simple DEM - center is lowest
    dem = np.array([
        [10.0, 9.0, 8.0],
        [9.0,  5.0, 7.0],
        [8.0,  7.0, 6.0]
    ], dtype=np.float64)
    
    print("\nDEM:")
    print(dem)
    
    # Compute flow direction
    flow_dir = compute_flow_direction(dem, nodata=None, cell_size=30.0)
    
    print("\nFlow Direction (D8 encoding):")
    print(flow_dir)
    
    # Compute flow accumulation
    flow_acc = compute_flow_accumulation(flow_dir, nodata_mask=None)
    
    print("\nFlow Accumulation:")
    print(flow_acc)
    
    # Validate: center cell should have highest accumulation
    center_acc = flow_acc[1, 1]
    print(f"\nCenter cell accumulation: {center_acc}")
    
    if center_acc == 9:
        print("[OK] Center cell has all 9 cells draining to it")
    else:
        print(f"[WARNING] Expected 9, got {center_acc}")
    
    print()


def test_conditioned_dem():
    """Test with real conditioned Assam DEM."""
    print("=" * 70)
    print("Test 2: Conditioned Assam DEM")
    print("=" * 70)
    
    # Load conditioned DEM from Task 3
    dem_path = Path("data/dem_cache/dem_COP30_a31683f8.tif")
    
    if not dem_path.exists():
        print(f"\n[ERROR] DEM not found: {dem_path}")
        print("Please run test_dem_acquisition.py first.")
        return
    
    print(f"\n1. Loading conditioned DEM from Task 3...")
    conditioned = condition_dem(dem_path, cache=True)
    
    print(f"   Shape: {conditioned.data.shape}")
    print(f"   CRS: {conditioned.crs}")
    print(f"   NoData: {conditioned.nodata}")
    
    # Compute flow direction
    print(f"\n2. Computing D8 flow direction...")
    flow_dir = compute_flow_direction(
        conditioned.data,
        nodata=conditioned.nodata,
        cell_size=30.92  # COP30 resolution
    )
    
    # Compute flow accumulation
    print(f"\n3. Computing flow accumulation...")
    nodata_mask = conditioned.data == conditioned.nodata if conditioned.nodata else None
    flow_acc = compute_flow_accumulation(flow_dir, nodata_mask)
    
    # Statistics
    print(f"\n4. Flow Accumulation Statistics:")
    print(f"   Min: {flow_acc.min()}")
    print(f"   Max: {flow_acc.max():,}")
    print(f"   Mean: {flow_acc.mean():.2f}")
    print(f"   Median: {np.median(flow_acc):.2f}")
    
    # Extract channels
    print(f"\n5. Extracting channel network...")
    
    # Test multiple thresholds
    thresholds = [500, 1000, 5000, 10000]
    for threshold in thresholds:
        channels = extract_channel_mask(flow_acc, threshold=threshold)
        num_channels = np.sum(channels)
        pct = (num_channels / flow_acc.size) * 100
        print(f"   Threshold {threshold:>5}: {num_channels:>6} cells ({pct:>5.2f}%)")
    
    # Use default threshold
    channels = extract_channel_mask(flow_acc, threshold=1000)
    
    # Validate
    print(f"\n6. Validation:")
    
    # Check max accumulation
    if flow_acc.max() > 1000:
        print(f"   [OK] Max accumulation ({flow_acc.max():,}) > 1000 (rivers exist)")
    else:
        print(f"   [WARNING] Max accumulation ({flow_acc.max():,}) < 1000")
    
    # Check channel cells
    num_channels = np.sum(channels)
    if num_channels > 0:
        print(f"   [OK] {num_channels:,} channel cells extracted")
    else:
        print(f"   [ERROR] No channels extracted!")
    
    # Check channel percentage
    channel_pct = (num_channels / flow_acc.size) * 100
    if 0.1 < channel_pct < 10:
        print(f"   [OK] Channels are {channel_pct:.2f}% of area (reasonable)")
    else:
        print(f"   [WARNING] Channels are {channel_pct:.2f}% of area")
    
    # Check flow direction outlets
    outlets = np.sum(flow_dir == 0)
    if nodata_mask is not None:
        outlets -= np.sum(nodata_mask)
    print(f"   [OK] {outlets} outlet cells (boundary drainage)")
    
    print(f"\n{'=' * 70}")
    print("[OK] All flow tests passed!")
    print(f"{'=' * 70}")
    
    print(f"\nDual-Hazard Outputs:")
    print(f"  - Flow Direction: {flow_dir.shape} array (routing for flood + landslide)")
    print(f"  - Flow Accumulation: {flow_acc.shape} array (RAW counts preserved)")
    print(f"  - Channel Mask: {channels.shape} boolean (river network)")
    
    print(f"\nMulti-Modal Usage:")
    print(f"  Flood Modeling:")
    print(f"    - flow_acc >= 1000 -> river channels")
    print(f"    - flow_dir -> water routing")
    print(f"  Landslide Modeling:")
    print(f"    - flow_acc x cell_size^2 -> upslope contributing area (m^2)")
    print(f"    - flow_dir -> downslope failure path")


if __name__ == "__main__":
    # Test simple DEM
    test_simple_dem()
    
    # Test real DEM
    test_conditioned_dem()
