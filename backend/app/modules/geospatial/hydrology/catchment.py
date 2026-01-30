"""
Catchment Delineation and Pour Point Snapping

Extracts upstream drainage basins for dual-hazard modeling:
- Flood: Rainfall aggregation areas for discharge forecasting
- Landslide: Upslope context and water loading zones

Key Features:
- GPS error correction via pour point snapping
- Upstream traversal for complete basin extraction
- Vector conversion for PostGIS storage and visualization

Author: NEXUS-AI Team
"""

from typing import Tuple, Optional, Dict
from collections import deque, defaultdict
import numpy as np
import rasterio.features
from rasterio.transform import Affine, rowcol
from pyproj import CRS

from app.core.logging import get_logger

logger = get_logger("catchment")


def latlon_to_grid(
    lat: float,
    lon: float,
    transform: Affine
) -> Tuple[int, int]:
    """
    Convert geographic coordinates to grid indices.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        transform: Affine transform from DEM
    
    Returns:
        Tuple of (row, col) grid indices
    
    Note:
        rowcol() expects (x, y) = (lon, lat) order
    """
    row, col = rowcol(transform, lon, lat)
    return int(row), int(col)


def snap_pour_point(
    lat: float,
    lon: float,
    flow_accumulation: np.ndarray,
    transform: Affine,
    search_radius: int = 5
) -> Tuple[int, int, float]:
    """
    Snap pour point to drainage network by finding max flow accumulation.
    
    Corrects GPS errors by searching for the cell with highest flow
    accumulation within a search window. Critical for accurate catchment
    delineation - a 1-pixel error can reduce basin from 10,000 km² to 10 m².
    
    Args:
        lat: Latitude of pour point (degrees)
        lon: Longitude of pour point (degrees)
        flow_accumulation: Flow accumulation array from Task 4
        transform: Affine transform from DEM
        search_radius: Search window radius in pixels (default 5 = ~150m for 30m DEM)
    
    Returns:
        Tuple of (snapped_row, snapped_col, snap_distance_pixels)
    
    Example:
        >>> # Gauge location (may have GPS error)
        >>> lat, lon = 26.1833, 91.7500
        >>> snapped_row, snapped_col, dist = snap_pour_point(
        ...     lat, lon, flow_acc, transform, search_radius=10
        ... )
        >>> print(f"Snapped {dist:.1f} pixels to river")
    """
    logger.info("snapping_pour_point", lat=lat, lon=lon, search_radius=search_radius)
    
    # Convert to grid indices
    orig_row, orig_col = latlon_to_grid(lat, lon, transform)
    
    rows, cols = flow_accumulation.shape
    
    # Define search window (bounded by grid)
    r_min = max(0, orig_row - search_radius)
    r_max = min(rows, orig_row + search_radius + 1)
    c_min = max(0, orig_col - search_radius)
    c_max = min(cols, orig_col + search_radius + 1)
    
    # Extract window
    window = flow_accumulation[r_min:r_max, c_min:c_max]
    
    # Find max accumulation in window
    max_idx = np.unravel_index(np.argmax(window), window.shape)
    
    # Convert back to full grid indices
    snapped_row = r_min + max_idx[0]
    snapped_col = c_min + max_idx[1]
    
    # Calculate snap distance
    snap_distance = np.sqrt((snapped_row - orig_row)**2 + (snapped_col - orig_col)**2)
    
    logger.info(
        "pour_point_snapped",
        original=(orig_row, orig_col),
        snapped=(snapped_row, snapped_col),
        snap_distance_pixels=round(float(snap_distance), 2),
        max_accumulation=int(flow_accumulation[snapped_row, snapped_col])
    )
    
    return snapped_row, snapped_col, float(snap_distance)


def delineate_catchment(
    snapped_point: Tuple[int, int],
    flow_direction: np.ndarray,
    nodata_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Delineate catchment by traversing upstream from pour point.
    
    Uses breadth-first search to find all cells that drain to the
    pour point. Includes full hillslope area (not just channels)
    for dual-hazard compatibility.
    
    Args:
        snapped_point: (row, col) of snapped pour point
        flow_direction: D8 flow direction array from Task 4
        nodata_mask: Optional boolean mask for NoData cells
    
    Returns:
        Boolean mask (True = cell in catchment)
    
    Example:
        >>> catchment = delineate_catchment(snapped_point, flow_dir)
        >>> area_cells = np.sum(catchment)
        >>> area_km2 = area_cells * (30.92 ** 2) / 1e6
        >>> print(f"Catchment area: {area_km2:.2f} km²")
    """
    logger.info("delineating_catchment", pour_point=snapped_point)
    
    rows, cols = flow_direction.shape
    catchment = np.zeros((rows, cols), dtype=bool)
    
    # Create NoData mask if not provided
    if nodata_mask is None:
        nodata_mask = np.zeros((rows, cols), dtype=bool)
    
    # Mark pour point
    pour_row, pour_col = snapped_point
    
    # Validate pour point
    if not (0 <= pour_row < rows and 0 <= pour_col < cols):
        logger.error("invalid_pour_point", point=snapped_point, shape=(rows, cols))
        raise ValueError(f"Pour point {snapped_point} outside grid bounds")
    
    if nodata_mask[pour_row, pour_col]:
        logger.error("pour_point_on_nodata", point=snapped_point)
        raise ValueError(f"Pour point {snapped_point} is on NoData cell")
    
    catchment[pour_row, pour_col] = True
    
    # Build upstream map (downstream -> upstream cells)
    logger.info("building_upstream_map")
    upstream_map = _build_upstream_map(flow_direction, nodata_mask)
    
    # BFS upstream
    logger.info("traversing_upstream")
    queue = deque([snapped_point])
    visited = {snapped_point}
    
    while queue:
        row, col = queue.popleft()
        
        # Get all cells that flow INTO this cell
        upstream_cells = upstream_map.get((row, col), [])
        
        for ur, uc in upstream_cells:
            if (ur, uc) not in visited:
                catchment[ur, uc] = True
                visited.add((ur, uc))
                queue.append((ur, uc))
    
    # Log statistics
    area_cells = int(np.sum(catchment))
    logger.info("catchment_delineated", area_cells=area_cells)
    
    return catchment


def _build_upstream_map(
    flow_direction: np.ndarray,
    nodata_mask: np.ndarray
) -> Dict[Tuple[int, int], list]:
    """
    Build map of downstream cell -> list of upstream cells.
    
    Args:
        flow_direction: D8 flow direction array
        nodata_mask: Boolean mask for NoData cells
    
    Returns:
        Dictionary mapping (row, col) -> [(upstream_row, upstream_col), ...]
    """
    upstream_map = defaultdict(list)
    
    # D8 direction codes to offsets
    dir_to_offset = {
        64: (-1, 0),   # North
        128: (-1, 1),  # Northeast
        1: (0, 1),     # East
        2: (1, 1),     # Southeast
        4: (1, 0),     # South
        8: (1, -1),    # Southwest
        16: (0, -1),   # West
        32: (-1, -1),  # Northwest
    }
    
    rows, cols = flow_direction.shape
    
    for i in range(rows):
        for j in range(cols):
            # Skip NoData cells
            if nodata_mask[i, j]:
                continue
            
            flow = flow_direction[i, j]
            
            # Skip outlets (flow = 0)
            if flow == 0:
                continue
            
            # Get downstream cell
            if flow in dir_to_offset:
                dr, dc = dir_to_offset[flow]
                di, dj = i + dr, j + dc
                
                # Validate downstream cell
                if 0 <= di < rows and 0 <= dj < cols and not nodata_mask[di, dj]:
                    # Cell (i,j) flows INTO cell (di,dj)
                    # So (i,j) is UPSTREAM of (di,dj)
                    upstream_map[(di, dj)].append((i, j))
    
    return upstream_map


def catchment_to_polygon(
    catchment_mask: np.ndarray,
    transform: Affine,
    crs: CRS
) -> Optional[dict]:
    """
    Convert raster catchment mask to GeoJSON polygon.
    
    Vectorizes the catchment for:
    - PostGIS storage (geometry column)
    - Frontend visualization (Leaflet/Mapbox)
    - Zonal statistics (rainfall aggregation)
    
    Args:
        catchment_mask: Boolean mask from delineate_catchment()
        transform: Affine transform from DEM
        crs: Coordinate reference system
    
    Returns:
        GeoJSON Feature dict with polygon geometry, or None if empty
    
    Example:
        >>> polygon = catchment_to_polygon(catchment, transform, crs)
        >>> # Save to PostGIS
        >>> db.execute("INSERT INTO catchments (geom) VALUES (ST_GeomFromGeoJSON(%s))",
        ...            json.dumps(polygon['geometry']))
    """
    logger.info("converting_to_polygon", area_cells=int(np.sum(catchment_mask)))
    
    if not np.any(catchment_mask):
        logger.warning("empty_catchment_mask")
        return None
    
    # Vectorize mask
    shapes = list(rasterio.features.shapes(
        catchment_mask.astype(np.uint8),
        transform=transform
    ))
    
    # Extract polygon (first shape with value=1)
    for geom, value in shapes:
        if value == 1:
            # Calculate area
            area_cells = int(np.sum(catchment_mask))
            
            # Get cell size from transform
            cell_size = abs(transform.a)  # Assuming square pixels
            area_deg2 = area_cells * (cell_size ** 2)
            
            # Approximate area in km² (rough, assumes equatorial)
            # For accurate area, use projected CRS
            area_km2_approx = area_deg2 * 111.32 * 111.32  # deg² to km² at equator
            
            polygon = {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "area_cells": area_cells,
                    "area_deg2": round(area_deg2, 6),
                    "area_km2_approx": round(area_km2_approx, 2),
                    "crs": crs.to_string()
                }
            }
            
            logger.info(
                "polygon_created",
                area_cells=area_cells,
                area_km2_approx=round(area_km2_approx, 2)
            )
            
            return polygon
    
    logger.warning("no_polygon_found")
    return None
