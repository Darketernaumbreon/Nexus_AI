"""
Test Script for HAND Computation & Flood Inundation Mapping

Tests:
1. HAND computation with validation
2. Flood mask generation at multiple water levels
3. Polygon conversion and area calculation
4. Multi-modal safety (read-only operations)
5. Visual validation with plots

Usage:
    python test_hand.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import json
from pathlib import Path

# Import hydrology modules
from app.modules.geospatial.hydrology.conditioning import condition_dem
from app.modules.geospatial.hydrology.flow import (
    compute_flow_direction,
    compute_flow_accumulation,
    extract_channel_mask
)
from app.modules.geospatial.hydrology.hand import (
    compute_hand,
    flood_mask,
    flood_polygon
)
from app.modules.geospatial.clients.opentopography import fetch_dem
from app.core.logging import get_logger

logger = get_logger("test_hand")


def test_hand_computation():
    """Test HAND computation with real Assam DEM."""
    print("\n" + "="*60)
    print("TEST 1: HAND Computation")
    print("="*60)
    
    # Fetch DEM (cached from previous tasks)
    # Assam region coordinates
    min_lat = 26.0
    max_lat = 26.2
    min_lon = 91.5
    max_lon = 91.7
    
    print("\n[1/6] Fetching DEM...")
    dem_path = fetch_dem(
        min_lat, min_lon,
        max_lat, max_lon
    )
    
    print(f"[OK] DEM fetched: {dem_path}")
    
    # Condition DEM
    print("\n[2/6] Conditioning DEM...")
    conditioned = condition_dem(dem_path, cache=True)
    
    print(f"[OK] DEM conditioned: {conditioned.data.shape}")
    
    # Compute flow direction
    print("\n[3/6] Computing flow direction...")
    flow_dir = compute_flow_direction(
        conditioned.data,
        nodata=conditioned.nodata,
        cell_size=30.92  # COP30 resolution
    )
    
    print(f"[OK] Flow direction computed")
    
    # Compute flow accumulation
    print("\n[4/6] Computing flow accumulation...")
    nodata_mask = (conditioned.data == conditioned.nodata) if conditioned.nodata is not None else None
    flow_acc = compute_flow_accumulation(flow_dir, nodata_mask=nodata_mask)
    
    print(f"[OK] Flow accumulation computed (max: {np.max(flow_acc)})")
    
    # Extract channels
    print("\n[5/6] Extracting channels...")
    channels = extract_channel_mask(flow_acc, threshold=1000)
    num_channels = np.sum(channels)
    
    print(f"[OK] Channels extracted: {num_channels} cells")
    
    # Compute HAND
    print("\n[6/6] Computing HAND...")
    hand = compute_hand(
        conditioned.data,
        flow_dir,
        channels,
        nodata_mask=nodata_mask
    )
    
    print(f"[OK] HAND computed")
    
    # Validation
    print("\n" + "-"*60)
    print("VALIDATION CHECKS:")
    print("-"*60)
    
    # Check 1: Channel cells have HAND = 0
    channel_hand = hand[channels]
    max_channel_hand = np.max(channel_hand)
    print(f"[OK] Max HAND in channels: {max_channel_hand:.6f} (should be ~0)")
    assert max_channel_hand < 0.01, "Channel cells should have HAND ~ 0"
    
    # Check 2: No negative HAND values
    min_hand = np.min(hand)
    print(f"[OK] Min HAND: {min_hand:.2f} (should be >= 0)")
    assert min_hand >= 0, "HAND should be non-negative"
    
    # Check 3: HAND statistics
    mean_hand = np.mean(hand)
    max_hand = np.max(hand)
    print(f"[OK] Mean HAND: {mean_hand:.2f} m")
    print(f"[OK] Max HAND: {max_hand:.2f} m")
    
    print("\n[PASS] HAND computation test PASSED")
    
    return {
        'hand': hand,
        'channels': channels,
        'dem': conditioned.data,
        'transform': conditioned.transform,
        'crs': conditioned.crs
    }


def test_flood_mask(hand_data):
    """Test flood mask generation at multiple water levels."""
    print("\n" + "="*60)
    print("TEST 2: Flood Mask Generation")
    print("="*60)
    
    hand = hand_data['hand']
    water_levels = [0.5, 1.0, 2.0, 3.0, 5.0]
    
    flood_masks = {}
    
    for wl in water_levels:
        print(f"\n[Water Level: {wl}m]")
        mask = flood_mask(hand, water_level_m=wl)
        num_flooded = np.sum(mask)
        pct_flooded = num_flooded / mask.size * 100
        
        print(f"  Flooded cells: {num_flooded} ({pct_flooded:.2f}%)")
        
        flood_masks[wl] = mask
    
    # Validation: flood extent should increase with water level
    print("\n" + "-"*60)
    print("VALIDATION CHECKS:")
    print("-"*60)
    
    prev_count = 0
    for wl in water_levels:
        count = np.sum(flood_masks[wl])
        print(f"[OK] Water level {wl}m: {count} cells")
        assert count >= prev_count, f"Flood extent should increase with water level"
        prev_count = count
    
    print("\n[PASS] Flood mask test PASSED")
    
    return flood_masks


def test_flood_polygon(hand_data, flood_masks):
    """Test polygon conversion and area calculation."""
    print("\n" + "="*60)
    print("TEST 3: Flood Polygon Conversion")
    print("="*60)
    
    transform = hand_data['transform']
    crs = hand_data['crs']
    
    # Test with 3m water level
    water_level = 3.0
    mask = flood_masks[water_level]
    
    print(f"\n[Converting flood mask at {water_level}m to polygon...]")
    polygon = flood_polygon(mask, transform, crs, simplify_tolerance=0.0001)
    
    # Validation
    print("\n" + "-"*60)
    print("VALIDATION CHECKS:")
    print("-"*60)
    
    print(f"[OK] GeoJSON type: {polygon['type']}")
    assert polygon['type'] == 'Feature', "Should be GeoJSON Feature"
    
    print(f"[OK] Geometry type: {polygon['geometry']['type']}")
    
    props = polygon['properties']
    print(f"[OK] Area: {props['area_km2']:.3f} km2")
    print(f"[OK] Area: {props['area_m2']:.1f} m2")
    print(f"[OK] Num cells: {props['num_cells']}")
    print(f"[OK] CRS: {props['crs']}")
    
    assert props['area_km2'] > 0, "Area should be positive"
    assert props['num_cells'] == np.sum(mask), "Cell count mismatch"
    
    # Save to file
    output_path = Path("test_flood_polygon.geojson")
    with open(output_path, 'w') as f:
        json.dump(polygon, f, indent=2)
    
    print(f"\n[OK] Polygon saved to: {output_path}")
    
    print("\n[PASS] Polygon conversion test PASSED")
    
    return polygon


def test_multi_modal_safety(hand_data):
    """Test that HAND computation doesn't modify input data."""
    print("\n" + "="*60)
    print("TEST 4: Multi-Modal Safety")
    print("="*60)
    
    # Create copies of original data
    dem_original = hand_data['dem'].copy()
    channels_original = hand_data['channels'].copy()
    
    # Compute HAND again
    print("\n[Re-computing HAND to verify read-only operations...]")
    hand_new = compute_hand(
        hand_data['dem'],
        np.zeros_like(hand_data['dem'], dtype=np.uint8),  # dummy flow dir
        hand_data['channels'],
        nodata_mask=None
    )
    
    # Validation
    print("\n" + "-"*60)
    print("VALIDATION CHECKS:")
    print("-"*60)
    
    dem_unchanged = np.array_equal(hand_data['dem'], dem_original)
    print(f"[OK] DEM unchanged: {dem_unchanged}")
    assert dem_unchanged, "DEM should not be modified"
    
    channels_unchanged = np.array_equal(hand_data['channels'], channels_original)
    print(f"[OK] Channels unchanged: {channels_unchanged}")
    assert channels_unchanged, "Channels should not be modified"
    
    print("\n[PASS] Multi-modal safety test PASSED")
    print("   -> HAND is safe for dual-hazard modeling (flood + landslide)")


def visualize_results(hand_data, flood_masks):
    """Create visual validation plots."""
    print("\n" + "="*60)
    print("TEST 5: Visual Validation")
    print("="*60)
    
    hand = hand_data['hand']
    channels = hand_data['channels']
    dem = hand_data['dem']
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('HAND Computation & Flood Inundation Mapping', fontsize=16, fontweight='bold')
    
    # 1. Original DEM
    ax = axes[0, 0]
    im1 = ax.imshow(dem, cmap='terrain')
    ax.set_title('1. Original DEM', fontweight='bold')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    plt.colorbar(im1, ax=ax, label='Elevation (m)')
    
    # 2. Channel Network
    ax = axes[0, 1]
    channel_display = np.where(channels, 1, 0)
    im2 = ax.imshow(channel_display, cmap='Blues')
    ax.set_title('2. Channel Network', fontweight='bold')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    plt.colorbar(im2, ax=ax, label='Channel (1=yes)')
    
    # 3. HAND Raster
    ax = axes[0, 2]
    # Custom colormap: blue (low) to red (high)
    colors = ['#0000ff', '#00ffff', '#00ff00', '#ffff00', '#ff0000']
    n_bins = 100
    cmap_hand = LinearSegmentedColormap.from_list('hand', colors, N=n_bins)
    
    im3 = ax.imshow(hand, cmap=cmap_hand)
    ax.set_title('3. HAND Raster', fontweight='bold')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    plt.colorbar(im3, ax=ax, label='HAND (m)')
    
    # 4-6. Flood Masks at different water levels
    water_levels = [1.0, 3.0, 5.0]
    for idx, wl in enumerate(water_levels):
        ax = axes[1, idx]
        mask = flood_masks[wl]
        
        # Overlay flood on DEM
        flood_display = np.ma.masked_where(~mask, dem)
        ax.imshow(dem, cmap='gray', alpha=0.5)
        im = ax.imshow(flood_display, cmap='Blues', alpha=0.8)
        
        num_flooded = np.sum(mask)
        pct_flooded = num_flooded / mask.size * 100
        
        ax.set_title(f'{idx+4}. Flood at {wl}m\n({num_flooded} cells, {pct_flooded:.1f}%)', 
                     fontweight='bold')
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')
        plt.colorbar(im, ax=ax, label='Flooded Area')
    
    plt.tight_layout()
    
    # Save figure
    output_path = Path("test_hand_visualization.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Visualization saved to: {output_path}")
    
    plt.show()
    
    print("\n[PASS] Visual validation complete")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("HAND COMPUTATION & FLOOD INUNDATION MAPPING TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: HAND computation
        hand_data = test_hand_computation()
        
        # Test 2: Flood mask generation
        flood_masks = test_flood_mask(hand_data)
        
        # Test 3: Polygon conversion
        polygon = test_flood_polygon(hand_data, flood_masks)
        
        # Test 4: Multi-modal safety
        test_multi_modal_safety(hand_data)
        
        # Test 5: Visual validation
        visualize_results(hand_data, flood_masks)
        
        print("\n" + "="*60)
        print("[PASS] ALL TESTS PASSED")
        print("="*60)
        print("\nKey Validations:")
        print("  [OK] Channel cells have HAND = 0")
        print("  [OK] No negative HAND values")
        print("  [OK] Flood extent increases with water level")
        print("  [OK] Valid GeoJSON polygon generated")
        print("  [OK] Multi-modal safe (read-only operations)")
        print("\nOutputs:")
        print("  -> test_flood_polygon.geojson")
        print("  -> test_hand_visualization.png")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
