"""
Grid-Based Dataset Builder for Landslide Prediction

Creates ML dataset on spatial grid cells (1km × 1km) with:
- Topographic features (slope, aspect, curvature)
- Weather features (rainfall, temperature)
- Landslide labels (binary, daily resolution)

Author: NEXUS-AI Team
"""

from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("dataset_builder_landslide")


def create_spatial_grid(
    bbox: Tuple[float, float, float, float],
    cell_size_km: float = 1.0
) -> gpd.GeoDataFrame:
    """
    Create uniform spatial grid over bounding box.
    
    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        cell_size_km: Grid cell size in kilometers
    
    Returns:
        GeoDataFrame with grid cells and metadata
    
    Example:
        >>> bbox = (89.0, 24.0, 96.0, 28.0)
        >>> grid = create_spatial_grid(bbox, cell_size_km=1.0)
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # Convert km to degrees (approximate: 1° ≈ 111 km)
    cell_size_deg = cell_size_km / 111.0
    
    # Create grid
    lons = np.arange(min_lon, max_lon, cell_size_deg)
    lats = np.arange(min_lat, max_lat, cell_size_deg)
    
    cells = []
    for i, lon in enumerate(lons):
        for j, lat in enumerate(lats):
            # Create cell polygon
            cell_bounds = [
                (lon, lat),
                (lon + cell_size_deg, lat),
                (lon + cell_size_deg, lat + cell_size_deg),
                (lon, lat + cell_size_deg),
                (lon, lat)
            ]
            polygon = Polygon(cell_bounds)
            
            # Cell center
            center_lon = lon + cell_size_deg / 2
            center_lat = lat + cell_size_deg / 2
            
            cells.append({
                'grid_id': f'CELL_{i:04d}_{j:04d}',
                'center_lon': center_lon,
                'center_lat': center_lat,
                'geometry': polygon
            })
    
    gdf = gpd.GeoDataFrame(cells, crs="EPSG:4326")
    
    logger.info(
        "grid_created",
        num_cells=len(gdf),
        cell_size_km=cell_size_km,
        bbox=bbox
    )
    
    return gdf


def extract_slope_features_mock(
    grid: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Extract slope features for each grid cell (MOCK VERSION).
    
    In production, this would use actual DEM rasterio extraction.
    For now, generates realistic synthetic slope/aspect values.
    
    Args:
        grid: Grid GeoDataFrame
    
    Returns:
        Grid with slope, aspect, curvature columns
    """
    logger.info("extracting_slope_features_mock", num_cells=len(grid))
    
    np.random.seed(42)
    
    # Generate realistic slope values (0-45 degrees, skewed towards lower)
    grid['slope'] = np.random.beta(2, 5, size=len(grid)) * 45
    
    # Aspect (0-360 degrees)
    grid['aspect'] = np.random.uniform(0, 360, size=len(grid))
    
    # Curvature (-0.1 to 0.1, mostly near 0)
    grid['curvature'] = np.random.normal(0, 0.02, size=len(grid))
    grid['curvature'] = np.clip(grid['curvature'], -0.1, 0.1)
    
    # Elevation (mock: 100-3000m)
    grid['elevation'] = np.random.uniform(100, 3000, size=len(grid))
    
    logger.info("slope_features_extracted_mock", features=['slope', 'aspect', 'curvature', 'elevation'])
    
    return grid


def spatial_join_landslides(
    grid: gpd.GeoDataFrame,
    landslides: pd.DataFrame,
    date_range: Tuple[datetime, datetime]
) -> pd.DataFrame:
    """
    Create daily labels for each grid cell based on landslide occurrences.
    
    Args:
        grid: Spatial grid
        landslides: Landslide inventory (lat, lon, date)
        date_range: (start_date, end_date) for daily labels
    
    Returns:
        DataFrame with columns: grid_id, date, label, num_events
    
    Schema:
        - label = 1 if ≥1 landslide in cell on that day
        - label = 0 otherwise
    """
    logger.info(
        "spatial_join_landslides",
        num_cells=len(grid),
        num_landslides=len(landslides),
        date_range=f"{date_range[0]} to {date_range[1]}"
    )
    
    # Convert landslides to GeoDataFrame
    landslides_gdf = gpd.GeoDataFrame(
        landslides,
        geometry=[Point(row['lon'], row['lat']) for _, row in landslides.iterrows()],
        crs="EPSG:4326"
    )
    
    # Spatial join: which grid cell does each landslide fall into?
    joined = gpd.sjoin(landslides_gdf, grid[['grid_id', 'geometry']], how='left', predicate='within')
    
    # Group by grid_id and date
    joined['date'] = pd.to_datetime(joined['date']).dt.date
    landslide_counts = joined.groupby(['grid_id', 'date']).size().reset_index(name='num_events')
    
    # Generate all grid_id × date combinations
    start_date, end_date = date_range
    dates = pd.date_range(start_date, end_date, freq='D').date
    
    all_combinations = []
    for grid_id in grid['grid_id']:
        for date in dates:
            all_combinations.append({'grid_id': grid_id, 'date': date})
    
    full_df = pd.DataFrame(all_combinations)
    
    # Merge with landslide counts
    full_df = full_df.merge(landslide_counts, on=['grid_id', 'date'], how='left')
    full_df['num_events'] = full_df['num_events'].fillna(0).astype(int)
    
    # Create binary label
    full_df['label'] = (full_df['num_events'] > 0).astype(int)
    
    # Convert date back to datetime
    full_df['date'] = pd.to_datetime(full_df['date'])
    
    logger.info(
        "labels_created",
        total_rows=len(full_df),
        positive_labels=int(full_df['label'].sum()),
        positive_rate=round(full_df['label'].mean() * 100, 3)
    )
    
    return full_df


def apply_negative_sampling(
    df: pd.DataFrame,
    ratio: int = 10,
    seed: int = 42
) -> pd.DataFrame:
    """
    Apply negative sampling to balance extreme class imbalance.
    
    Strategy:
    - Keep ALL positive samples (label=1)
    - Sample negatives at specified ratio
    
    Args:
        df: Full dataset
        ratio: Negative:positive ratio (default 10:1)
        seed: Random seed
    
    Returns:
        Balanced dataset
    """
    logger.info("applying_negative_sampling", ratio=f"1:{ratio}")
    
    positives = df[df['label'] == 1]
    negatives = df[df['label'] == 0]
    
    num_positives = len(positives)
    num_negatives_to_sample = num_positives * ratio
    
    if num_negatives_to_sample >= len(negatives):
        # Not enough negatives, use all
        sampled_negatives = negatives
        logger.warning("insufficient_negatives", requested=num_negatives_to_sample, available=len(negatives))
    else:
        sampled_negatives = negatives.sample(n=num_negatives_to_sample, random_state=seed)
    
    balanced = pd.concat([positives, sampled_negatives], ignore_index=True)
    balanced = balanced.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    logger.info(
        "negative_sampling_complete",
        original_rows=len(df),
        balanced_rows=len(balanced),
        positive_rate=round(balanced['label'].mean() * 100, 2)
    )
    
    return balanced


def build_landslide_dataset(
    bbox: Tuple[float, float, float, float],
    start_date: datetime,
    end_date: datetime,
    landslides: pd.DataFrame,
    cell_size_km: float = 1.0,
    negative_sampling_ratio: int = 10
) -> pd.DataFrame:
    """
    Build complete landslide ML dataset.
    
    Args:
        bbox: Spatial extent
        start_date: Start date
        end_date: End date
        landslides: Landslide inventory
        cell_size_km: Grid cell size
        negative_sampling_ratio: Negative:positive ratio
    
    Returns:
        ML-ready dataset with features and labels
    """
    logger.info(
        "building_landslide_dataset",
        bbox=bbox,
        date_range=f"{start_date} to {end_date}",
        landslides=len(landslides)
    )
    
    # 1. Create spatial grid
    grid = create_spatial_grid(bbox, cell_size_km)
    
    # 2. Extract slope features (mock)
    grid = extract_slope_features_mock(grid)
    
    # 3. Create labels
    labels_df = spatial_join_landslides(grid, landslides, (start_date, end_date))
    
    # 4. Join grid features
    grid_features = grid[['grid_id', 'center_lon', 'center_lat', 'slope', 'aspect', 'curvature', 'elevation']]
    dataset = labels_df.merge(grid_features, on='grid_id', how='left')
    
    # 5. Add mock weather data (simplified for Task 9B demo)
    # In production, this would fetch from Open-Meteo API via weather_cache
    logger.info("adding_mock_weather_data")
    
    dataset['rainfall_mm'] = np.random.exponential(2, size=len(dataset))
    dataset['temperature'] = np.random.uniform(15, 35, size=len(dataset))
    
    # 6. Apply negative sampling
    dataset = apply_negative_sampling(dataset, ratio=negative_sampling_ratio)
    
    logger.info(
        "dataset_complete",
        total_rows=len(dataset),
        num_features=len(dataset.columns) - 2,  # Exclude grid_id, label
        positive_rate=round(dataset['label'].mean() * 100, 2)
    )
    
    return dataset
