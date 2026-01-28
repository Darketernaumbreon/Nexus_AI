"""
Flow Direction and Accumulation for River Network Extraction

Implements D8 flow routing and accumulation for dual-hazard modeling:
- Flood: River channel identification and routing
- Landslide: Upslope contributing area and water loading

CRITICAL: Flow accumulation is preserved as RAW CELL COUNTS.
Do NOT normalize, log-transform, or clip. Both hazards need raw values.

Author: NEXUS-AI Team
"""

from typing import Optional, Tuple
import numpy as np
from collections import deque

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("flow")


# D8 Flow Direction Encoding (ESRI convention)
# Each value represents flow to one of 8 neighbors
# 0 = no flow (pit or outlet)
#
#   32  64  128
#   16  [0]   1
#    8   4    2
#
# Neighbor offsets: (row_offset, col_offset, direction_code, distance_multiplier)
D8_NEIGHBORS = [
    (-1,  0, 64, 1.0),      # North
    (-1,  1, 128, 1.414),   # Northeast (diagonal)
    ( 0,  1, 1, 1.0),       # East
    ( 1,  1, 2, 1.414),     # Southeast (diagonal)
    ( 1,  0, 4, 1.0),       # South
    ( 1, -1, 8, 1.414),     # Southwest (diagonal)
    ( 0, -1, 16, 1.0),      # West
    (-1, -1, 32, 1.414),    # Northwest (diagonal)
]


def compute_flow_direction(
    conditioned_dem: np.ndarray,
    nodata: Optional[float] = None,
    cell_size: float = 30.0
) -> np.ndarray:
    """
    Compute D8 flow direction using steepest descent.
    
    Each cell routes flow to ONE of its 8 neighbors based on
    steepest downward slope. Uses ESRI D8 encoding.
    
    Args:
        conditioned_dem: Hydrologically conditioned DEM (2D array)
        nodata: NoData value to exclude from flow
        cell_size: Cell resolution in meters (for slope calculation)
    
    Returns:
        2D array of D8 flow directions (uint8)
        - 0 = no flow (outlet or nodata)
        - 1,2,4,8,16,32,64,128 = flow to neighbor
    
    Example:
        >>> flow_dir = compute_flow_direction(conditioned_dem, nodata=None, cell_size=30.92)
        >>> # Use for accumulation
        >>> flow_acc = compute_flow_accumulation(flow_dir, nodata_mask)
    """
    logger.info("computing_flow_direction", shape=conditioned_dem.shape, cell_size=cell_size)
    
    rows, cols = conditioned_dem.shape
    flow_direction = np.zeros((rows, cols), dtype=np.uint8)
    
    # Create NoData mask
    if nodata is not None:
        nodata_mask = conditioned_dem == nodata
    else:
        nodata_mask = np.zeros((rows, cols), dtype=bool)
    
    # Compute flow direction for each cell
    for i in range(rows):
        for j in range(cols):
            # Skip NoData cells
            if nodata_mask[i, j]:
                flow_direction[i, j] = 0
                continue
            
            elevation = conditioned_dem[i, j]
            max_slope = -np.inf
            flow_dir = 0
            
            # Check all 8 neighbors
            for dr, dc, code, dist_mult in D8_NEIGHBORS:
                ni, nj = i + dr, j + dc
                
                # Check if neighbor is valid
                if 0 <= ni < rows and 0 <= nj < cols:
                    # Skip NoData neighbors
                    if nodata_mask[ni, nj]:
                        continue
                    
                    neighbor_elev = conditioned_dem[ni, nj]
                    
                    # Calculate slope (positive = downward)
                    distance = cell_size * dist_mult
                    slope = (elevation - neighbor_elev) / distance
                    
                    # Select steepest descent
                    if slope > max_slope:
                        max_slope = slope
                        flow_dir = code
            
            # Set flow direction
            # If no downslope neighbor found, flow_dir = 0 (outlet)
            flow_direction[i, j] = flow_dir
    
    # Log statistics
    outlets = np.sum(flow_direction == 0) - np.sum(nodata_mask)
    logger.info(
        "flow_direction_computed",
        outlets=int(outlets),
        nodata_cells=int(np.sum(nodata_mask))
    )
    
    return flow_direction


def compute_flow_accumulation(
    flow_direction: np.ndarray,
    nodata_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Compute flow accumulation using topological sorting.
    
    Accumulation = number of upstream cells draining into a cell (including itself).
    
    CRITICAL: Returns RAW CELL COUNTS (not normalized, not log-transformed).
    This is required for:
    - Flood: Channel threshold detection
    - Landslide: Upslope water loading features
    
    Algorithm: Topological sort ensures upstream cells processed before downstream.
    Complexity: O(n) where n = number of cells.
    
    Args:
        flow_direction: D8 flow direction array from compute_flow_direction()
        nodata_mask: Boolean mask for NoData cells (optional)
    
    Returns:
        2D array of flow accumulation (int32)
        - Each cell = 1 + sum(upstream contributors)
        - NoData cells = 0
    
    Example:
        >>> flow_acc = compute_flow_accumulation(flow_dir, nodata_mask)
        >>> # For flood: extract channels
        >>> channels = extract_channel_mask(flow_acc, threshold=1000)
        >>> # For landslide: use as feature
        >>> upslope_area = flow_acc * cell_size**2  # convert to m²
    """
    logger.info("computing_flow_accumulation", shape=flow_direction.shape)
    
    rows, cols = flow_direction.shape
    accumulation = np.zeros((rows, cols), dtype=np.int32)
    
    # Create NoData mask if not provided
    if nodata_mask is None:
        nodata_mask = np.zeros((rows, cols), dtype=bool)
    
    # Build reverse flow graph (downstream -> upstream)
    # This allows us to find all cells that flow INTO each cell
    upstream_cells = {}
    for i in range(rows):
        for j in range(cols):
            upstream_cells[(i, j)] = []
    
    # Map flow direction codes to offsets
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
    
    # Build upstream graph
    for i in range(rows):
        for j in range(cols):
            if nodata_mask[i, j]:
                continue
            
            flow_dir = flow_direction[i, j]
            
            if flow_dir == 0:
                # Outlet - no downstream cell
                continue
            
            # Find downstream cell
            if flow_dir in dir_to_offset:
                dr, dc = dir_to_offset[flow_dir]
                di, dj = i + dr, j + dc
                
                if 0 <= di < rows and 0 <= dj < cols:
                    # Add current cell to downstream cell's upstream list
                    upstream_cells[(di, dj)].append((i, j))
    
    # Topological sort using Kahn's algorithm
    # Count how many upstream cells each cell has
    indegree = np.zeros((rows, cols), dtype=np.int32)
    for i in range(rows):
        for j in range(cols):
            if not nodata_mask[i, j]:
                indegree[i, j] = len(upstream_cells[(i, j)])
    
    # Initialize all cells with 1 (the cell itself)
    for i in range(rows):
        for j in range(cols):
            if not nodata_mask[i, j]:
                accumulation[i, j] = 1
    
    # Initialize queue with cells that have no upstream (indegree = 0)
    queue = deque()
    for i in range(rows):
        for j in range(cols):
            if not nodata_mask[i, j] and indegree[i, j] == 0:
                queue.append((i, j))
    
    # Process cells in topological order
    processed = 0
    while queue:
        i, j = queue.popleft()
        processed += 1
        
        # Find downstream cell
        flow_dir = flow_direction[i, j]
        
        if flow_dir != 0 and flow_dir in dir_to_offset:
            dr, dc = dir_to_offset[flow_dir]
            di, dj = i + dr, j + dc
            
            if 0 <= di < rows and 0 <= dj < cols and not nodata_mask[di, dj]:
                # Add current cell's accumulation to downstream
                accumulation[di, dj] += accumulation[i, j]
                
                # Decrease indegree of downstream cell
                indegree[di, dj] -= 1
                
                # If all upstream cells processed, add to queue
                if indegree[di, dj] == 0:
                    queue.append((di, dj))
    
    # Log statistics
    max_acc = int(np.max(accumulation))
    mean_acc = float(np.mean(accumulation[~nodata_mask])) if np.any(~nodata_mask) else 0.0
    
    logger.info(
        "flow_accumulation_computed",
        max_accumulation=max_acc,
        mean_accumulation=round(mean_acc, 2),
        cells_processed=processed
    )
    
    return accumulation


def extract_channel_mask(
    flow_accumulation: np.ndarray,
    threshold: Optional[int] = None
) -> np.ndarray:
    """
    Extract channel network using flow accumulation threshold.
    
    Channels are defined as cells where flow accumulation >= threshold.
    
    Threshold Guidelines:
    - Small streams: 100-500 cells
    - Rivers: 1000-5000 cells
    - Major rivers: >10,000 cells
    
    Args:
        flow_accumulation: Flow accumulation array (raw cell counts)
        threshold: Minimum accumulation for channel (default from config)
    
    Returns:
        Boolean mask (True = channel cell)
    
    Example:
        >>> channels = extract_channel_mask(flow_acc, threshold=1000)
        >>> num_channels = np.sum(channels)
        >>> print(f"Channel cells: {num_channels}")
    """
    if threshold is None:
        threshold = settings.FLOW_ACCUMULATION_THRESHOLD
    
    logger.info("extracting_channels", threshold=threshold)
    
    # Simple threshold
    channels = flow_accumulation >= threshold
    
    num_channels = int(np.sum(channels))
    logger.info("channels_extracted", num_cells=num_channels)
    
    return channels
