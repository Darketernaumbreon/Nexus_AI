"""
HAND (Height Above Nearest Drainage) Computation for Flood Inundation Mapping

Computes elevation above nearest channel for flood extent prediction.
This is a geometric computation (NOT hydrodynamic simulation).

HAND is flood-specific and does NOT interfere with landslide modeling.
The conditioned DEM, slope, and flow accumulation remain untouched.

Key Functions:
- compute_hand: Trace downstream to nearest channel, compute elevation difference
- flood_mask: Generate inundation mask for given water level
- flood_polygon: Convert raster mask to GeoJSON polygon

Author: NEXUS-AI Team
"""

from typing import Optional, Dict, Any, Tuple
import numpy as np
import rasterio.features
from rasterio.transform import Affine
from pyproj import CRS
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

from app.core.logging import get_logger

logger = get_logger("hand")


# D8 direction to offset mapping (from flow.py)
D8_DIR_TO_OFFSET = {
    64: (-1, 0),   # North
    128: (-1, 1),  # Northeast
    1: (0, 1),     # East
    2: (1, 1),     # Southeast
    4: (1, 0),     # South
    8: (1, -1),    # Southwest
    16: (0, -1),   # West
    32: (-1, -1),  # Northwest
}


def compute_hand(
    conditioned_dem: np.ndarray,
    flow_direction: np.ndarray,
    channel_mask: np.ndarray,
    nodata_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Compute HAND (Height Above Nearest Drainage) raster using topological sorting.
    
    OPTIMIZED ALGORITHM (O(n) complexity):
    - Uses topological sort to process cells from channels upstream
    - Each cell computes HAND from its downstream neighbor in O(1)
    - Total complexity: O(n) instead of O(n²)
    
    For each cell, trace downstream using flow direction until a channel
    is reached. HAND = elevation(cell) - elevation(channel).
    
    This is pure geometry, NOT hydrodynamic simulation.
    
    Args:
        conditioned_dem: Hydrologically conditioned DEM (2D array)
        flow_direction: D8 flow direction array (from flow.py)
        channel_mask: Boolean mask of channel cells (from extract_channel_mask)
        nodata_mask: Optional boolean mask for NoData cells
    
    Returns:
        2D array of HAND values (float32)
        - HAND = 0 for channel cells
        - HAND >= 0 for all valid cells
        - HAND = 0 for NoData cells (masked out)
    
    Example:
        >>> hand = compute_hand(dem, flow_dir, channels, nodata_mask)
        >>> assert np.all(hand[channels] == 0)  # Channels have HAND=0
        >>> assert np.all(hand >= 0)  # No negative values
    """
    logger.info("computing_hand", shape=conditioned_dem.shape)
    
    rows, cols = conditioned_dem.shape
    hand = np.zeros((rows, cols), dtype=np.float32)
    
    # Create NoData mask if not provided
    if nodata_mask is None:
        nodata_mask = np.zeros((rows, cols), dtype=bool)
    
    # Build upstream map (reverse flow graph)
    # downstream_cell -> [upstream_cell1, upstream_cell2, ...]
    upstream_map = {}
    for i in range(rows):
        for j in range(cols):
            upstream_map[(i, j)] = []
    
    # Populate upstream map
    for i in range(rows):
        for j in range(cols):
            if nodata_mask[i, j]:
                continue
            
            flow_dir = flow_direction[i, j]
            
            # Skip if no flow (outlet)
            if flow_dir == 0:
                continue
            
            # Find downstream cell
            if flow_dir in D8_DIR_TO_OFFSET:
                dr, dc = D8_DIR_TO_OFFSET[flow_dir]
                di, dj = i + dr, j + dc
                
                if 0 <= di < rows and 0 <= dj < cols and not nodata_mask[di, dj]:
                    # Add current cell to downstream cell's upstream list
                    upstream_map[(di, dj)].append((i, j))
    
    # Initialize HAND for channel cells (they are the "outlets" for HAND computation)
    # Also initialize cells with no downstream (edge outlets)
    from collections import deque
    queue = deque()
    
    for i in range(rows):
        for j in range(cols):
            if nodata_mask[i, j]:
                hand[i, j] = 0.0
                continue
            
            # Channel cells have HAND = 0
            if channel_mask[i, j]:
                hand[i, j] = 0.0
                queue.append((i, j))
                continue
            
            # Cells that flow out of bounds or to NoData also get HAND = 0
            # (they are treated as outlets)
            flow_dir = flow_direction[i, j]
            
            if flow_dir == 0:
                # Outlet cell
                hand[i, j] = 0.0
                queue.append((i, j))
                continue
            
            if flow_dir in D8_DIR_TO_OFFSET:
                dr, dc = D8_DIR_TO_OFFSET[flow_dir]
                di, dj = i + dr, j + dc
                
                # Check if flows out of bounds or to NoData
                if not (0 <= di < rows and 0 <= dj < cols) or nodata_mask[di, dj]:
                    # Edge outlet - treat as channel
                    hand[i, j] = 0.0
                    queue.append((i, j))
    
    # Track which cells have been processed
    processed = np.zeros((rows, cols), dtype=bool)
    for i, j in queue:
        processed[i, j] = True
    
    # Process cells in topological order (from channels/outlets upstream)
    cells_processed = len(queue)
    
    while queue:
        i, j = queue.popleft()
        
        # Process all upstream cells
        for ui, uj in upstream_map[(i, j)]:
            if processed[ui, uj]:
                continue
            
            # Compute HAND for upstream cell
            # HAND[upstream] = (elevation[upstream] - elevation[downstream]) + HAND[downstream]
            elevation_diff = conditioned_dem[ui, uj] - conditioned_dem[i, j]
            hand[ui, uj] = max(0.0, elevation_diff + hand[i, j])
            
            # Mark as processed
            processed[ui, uj] = True
            cells_processed += 1
            
            # Add to queue
            queue.append((ui, uj))
    
    # Validation
    channel_hand_values = hand[channel_mask]
    if len(channel_hand_values) > 0:
        max_channel_hand = float(np.max(channel_hand_values))
        if max_channel_hand > 0.01:
            logger.warning("channel_hand_nonzero", max_value=max_channel_hand)
    
    min_hand = float(np.min(hand[~nodata_mask])) if np.any(~nodata_mask) else 0.0
    max_hand = float(np.max(hand[~nodata_mask])) if np.any(~nodata_mask) else 0.0
    mean_hand = float(np.mean(hand[~nodata_mask])) if np.any(~nodata_mask) else 0.0
    
    logger.info(
        "hand_computed",
        cells_processed=cells_processed,
        min_hand=round(min_hand, 2),
        max_hand=round(max_hand, 2),
        mean_hand=round(mean_hand, 2)
    )
    
    return hand


def flood_mask(
    hand_raster: np.ndarray,
    water_level_m: float,
    nodata_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Generate flood inundation mask for a given water level.
    
    Simple threshold: flooded = HAND < water_level
    
    Args:
        hand_raster: HAND raster from compute_hand()
        water_level_m: Water level above channel in meters
        nodata_mask: Optional boolean mask for NoData cells
    
    Returns:
        Boolean mask (True = flooded cell)
    
    Example:
        >>> flooded_3m = flood_mask(hand, water_level_m=3.0)
        >>> flooded_5m = flood_mask(hand, water_level_m=5.0)
        >>> assert np.sum(flooded_5m) > np.sum(flooded_3m)  # More area flooded
    """
    logger.info("generating_flood_mask", water_level_m=water_level_m)
    
    # Create NoData mask if not provided
    if nodata_mask is None:
        nodata_mask = np.zeros(hand_raster.shape, dtype=bool)
    
    # Simple threshold
    flooded = (hand_raster < water_level_m) & (~nodata_mask)
    
    num_flooded = int(np.sum(flooded))
    total_valid = int(np.sum(~nodata_mask))
    pct_flooded = (num_flooded / total_valid * 100) if total_valid > 0 else 0.0
    
    logger.info(
        "flood_mask_generated",
        flooded_cells=num_flooded,
        percent_flooded=round(pct_flooded, 2)
    )
    
    return flooded


def flood_polygon(
    flood_mask: np.ndarray,
    transform: Affine,
    crs: CRS,
    simplify_tolerance: float = 0.0001
) -> Dict[str, Any]:
    """
    Convert flood mask to GeoJSON polygon.
    
    Merges connected flooded regions and computes area metadata.
    Output is suitable for PostGIS storage and frontend visualization.
    
    Args:
        flood_mask: Boolean flood mask from flood_mask()
        transform: Affine transform from DEM
        crs: Coordinate reference system
        simplify_tolerance: Tolerance for polygon simplification (degrees)
    
    Returns:
        GeoJSON Feature dict with:
        - geometry: Polygon or MultiPolygon
        - properties: {area_km2, area_m2, num_cells}
    
    Example:
        >>> polygon = flood_polygon(flooded, transform, crs)
        >>> assert polygon['type'] == 'Feature'
        >>> assert 'area_km2' in polygon['properties']
        >>> # Store in PostGIS
        >>> db.execute("INSERT INTO flood_extents (geom) VALUES (ST_GeomFromGeoJSON(%s))",
        ...            json.dumps(polygon['geometry']))
    """
    logger.info("vectorizing_flood_polygon", flooded_cells=int(np.sum(flood_mask)))
    
    # Convert boolean mask to uint8 (required by rasterio.features)
    mask_uint8 = flood_mask.astype(np.uint8)
    
    # Extract shapes (polygons) from raster
    # shapes() returns generator of (geometry, value) tuples
    shapes_gen = rasterio.features.shapes(
        mask_uint8,
        mask=mask_uint8 == 1,
        transform=transform
    )
    
    # Convert to shapely geometries
    geometries = []
    for geom_dict, value in shapes_gen:
        if value == 1:  # Flooded cells
            geom = shape(geom_dict)
            geometries.append(geom)
    
    if not geometries:
        logger.warning("no_flood_polygons_found")
        # Return empty feature
        return {
            "type": "Feature",
            "geometry": None,
            "properties": {
                "area_km2": 0.0,
                "area_m2": 0.0,
                "num_cells": 0,
                "crs": crs.to_string()
            }
        }
    
    # Merge all polygons into single geometry
    if len(geometries) == 1:
        merged_geom = geometries[0]
    else:
        merged_geom = unary_union(geometries)
    
    # Simplify polygon to reduce size
    if simplify_tolerance > 0:
        merged_geom = merged_geom.simplify(simplify_tolerance, preserve_topology=True)
    
    # Compute area
    # Note: For geographic CRS (lat/lon), area is in square degrees
    # For projected CRS (UTM), area is in square meters
    area_deg2 = merged_geom.area
    
    # Approximate conversion to m² (rough estimate for lat/lon)
    # 1 degree ≈ 111 km at equator
    # For accurate area, should reproject to equal-area projection
    if crs.is_geographic:
        # Rough approximation
        area_m2 = area_deg2 * (111000 ** 2)
    else:
        # Projected CRS (already in meters)
        area_m2 = area_deg2
    
    area_km2 = area_m2 / 1e6
    
    # Create GeoJSON Feature
    feature = {
        "type": "Feature",
        "geometry": mapping(merged_geom),
        "properties": {
            "area_km2": round(area_km2, 3),
            "area_m2": round(area_m2, 1),
            "num_cells": int(np.sum(flood_mask)),
            "crs": crs.to_string()
        }
    }
    
    logger.info(
        "flood_polygon_created",
        area_km2=round(area_km2, 3),
        num_polygons=len(geometries)
    )
    
    return feature
