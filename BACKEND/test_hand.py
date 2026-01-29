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
import pytest

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


@pytest.fixture(scope="module")
def shared_hand_data():
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
    # ... (Validations kept as assertions in the fixture setup)
    channel_hand = hand[channels]
    assert np.max(channel_hand) < 0.01, "Channel cells should have HAND ~ 0"
    assert np.min(hand) >= 0, "HAND should be non-negative"

    return {
        'hand': hand,
        'channels': channels,
        'dem': conditioned.data,
        'transform': conditioned.transform,
        'crs': conditioned.crs
    }


@pytest.fixture(scope="module")
def shared_flood_masks(shared_hand_data):
    """Test flood mask generation at multiple water levels."""
    print("\n" + "="*60)
    print("TEST 2: Flood Mask Generation")
    print("="*60)
    
    hand = shared_hand_data['hand']
    water_levels = [0.5, 1.0, 2.0, 3.0, 5.0]
    
    flood_masks = {}
    
    prev_count = 0
    for wl in water_levels:
        mask = flood_mask(hand, water_level_m=wl)
        count = np.sum(mask)
        flood_masks[wl] = mask
        assert count >= prev_count, f"Flood extent should increase with water level"
        prev_count = count
    
    return flood_masks


def test_flood_polygon(shared_hand_data, shared_flood_masks):
    """Test polygon conversion and area calculation."""
    print("\n" + "="*60)
    print("TEST 3: Flood Polygon Conversion")
    print("="*60)
    
    transform = shared_hand_data['transform']
    crs = shared_hand_data['crs']
    
    # Test with 3m water level
    water_level = 3.0
    mask = shared_flood_masks[water_level]
    
    print(f"\n[Converting flood mask at {water_level}m to polygon...]")
    polygon = flood_polygon(mask, transform, crs, simplify_tolerance=0.0001)
    
    # Validation
    props = polygon['properties']
    assert props['area_km2'] > 0, "Area should be positive"
    assert props['num_cells'] == np.sum(mask), "Cell count mismatch"
    
    # Save to file
    output_path = Path("test_flood_polygon.geojson")
    with open(output_path, 'w') as f:
        json.dump(polygon, f, indent=2)
    
    return polygon


def test_multi_modal_safety(shared_hand_data):
    """Test that HAND computation doesn't modify input data."""
    print("\n" + "="*60)
    print("TEST 4: Multi-Modal Safety")
    print("="*60)
    
    # Create copies of original data
    dem_original = shared_hand_data['dem'].copy()
    channels_original = shared_hand_data['channels'].copy()
    
    # Compute HAND again
    hand_new = compute_hand(
        shared_hand_data['dem'],
        np.zeros_like(shared_hand_data['dem'], dtype=np.uint8),  # dummy flow dir
        shared_hand_data['channels'],
        nodata_mask=None
    )
    
    dem_unchanged = np.array_equal(shared_hand_data['dem'], dem_original)
    assert dem_unchanged, "DEM should not be modified"
    
    channels_unchanged = np.array_equal(shared_hand_data['channels'], channels_original)
    assert channels_unchanged, "Channels should not be modified"


def test_visualization(shared_hand_data, shared_flood_masks):
    """Create visual validation plots."""
    print("\n" + "="*60)
    print("TEST 5: Visual Validation")
    print("="*60)
    
    hand = shared_hand_data['hand']
    channels = shared_hand_data['channels']
    dem = shared_hand_data['dem']
    flood_masks = shared_flood_masks
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('HAND Computation & Flood Inundation Mapping', fontsize=16, fontweight='bold')
    
    # 1. DEM
    ax = axes[0, 0]
    im = ax.imshow(dem, cmap='terrain', aspect='equal')
    ax.set_title('Raw DEM (COP30)')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    
    # 2. Channels
    ax = axes[0, 1]
    im = ax.imshow(channels, cmap='Blues', interpolation='nearest', aspect='equal')
    ax.set_title('Extracted River Channels')
    
    # 3. HAND
    ax = axes[0, 2]
    im = ax.imshow(hand, cmap='gist_earth_r', aspect='equal')
    ax.set_title('HAND Model (Height Above Nearest Drainage)')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    
    # 4. Flood Mask (Low - 1m)
    ax = axes[1, 0]
    mask_1m = flood_masks[1.0]
    im = ax.imshow(mask_1m, cmap='Blues', aspect='equal')
    ax.set_title('Flood Inundation (1.0m)')
    
    # 5. Flood Mask (High - 5m)
    ax = axes[1, 1]
    mask_5m = flood_masks[5.0]
    im = ax.imshow(mask_5m, cmap='Reds', aspect='equal')
    ax.set_title('Flood Inundation (5.0m)')
    
    # 6. Flood Depth (5m) - Masked HAND
    ax = axes[1, 2]
    # Depth = water_level - HAND (where HAND < water_level)
    depth = np.where(mask_5m, 5.0 - hand, np.nan)
    im = ax.imshow(depth, cmap='Blues', aspect='equal')
    ax.set_title('Flood Depth Map (5.0m)')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save figure
    output_path = Path("test_hand_visualization.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Visualization saved to: {output_path}")
    
    # plt.show() # Disabled for CI
