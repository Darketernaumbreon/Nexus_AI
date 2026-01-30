"""
Dataset Builder for Flood Prediction Model

Joins weather features, terrain features, and flood labels into ML-ready datasets.

Author: NEXUS-AI Team
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.environmental.tasks.cwc_scraper import fetch_and_label_cwc_data
from app.modules.environmental.tasks.etl import fetch_historical_weather

logger = get_logger("dataset_builder")


def extract_terrain_features(catchment_polygon: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract static terrain features from catchment polygon.
    
    Args:
        catchment_polygon: GeoJSON polygon representing catchment
    
    Returns:
        Dictionary of terrain features
    
    Example:
        >>> features = extract_terrain_features(catchment_geojson)
        >>> print(features['catchment_area'])
    """
    from shapely.geometry import shape
    
    geom = shape(catchment_polygon)
    
    # Calculate area in km²
    minx, miny, maxx, maxy = geom.bounds
    avg_lat = (miny + maxy) / 2
    
    import math
    lat_correction = math.cos(math.radians(avg_lat))
    area_deg2 = geom.area
    area_km2 = area_deg2 * (111 ** 2) * lat_correction
    
    # For now, return basic terrain features
    # In production, compute actual HAND values from Tasks 2-6
    terrain_features = {
        'catchment_area': area_km2,
        'mean_hand': 5.0,  # Mock value - would compute from HAND raster
        'mean_slope': 2.5,  # Mock value - would compute from DEM
    }
    
    logger.info(
        "terrain_features_extracted",
        area_km2=round(area_km2, 2),
        features=list(terrain_features.keys())
    )
    
    return terrain_features


def build_flood_dataset(
    station_ids: List[str],
    start_date: datetime,
    end_date: datetime,
    catchment_polygons: Optional[Dict[str, Dict]] = None
) -> pd.DataFrame:
    """
    Build ML-ready flood dataset by joining weather, terrain, and labels.
    
    Args:
        station_ids: List of gauge station IDs
        start_date: Start date for data
        end_date: End date for data
        catchment_polygons: Optional dict mapping station_id -> GeoJSON polygon
    
    Returns:
        DataFrame with columns:
            timestamp, station_id, rainfall_mm, temperature_2m,
            catchment_area, mean_hand, mean_slope,
            water_level, warning_level, danger_level, label, quality_flag, ...
    
    Example:
        >>> df = build_flood_dataset(
        ...     station_ids=["GUW001"],
        ...     start_date=datetime(2024, 6, 1),
        ...     end_date=datetime(2024, 6, 7)
        ... )
        >>> print(df.head())
    """
    logger.info(
        "building_flood_dataset",
        num_stations=len(station_ids),
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    all_station_data = []
    
    for station_id in station_ids:
        logger.info("processing_station", station_id=station_id)
        
        # 1. Fetch flood labels (gauge data)
        try:
            gauge_df = fetch_and_label_cwc_data(station_id, start_date, end_date, clean=True)
        except Exception as e:
            logger.error("gauge_fetch_failed", station_id=station_id, error=str(e))
            continue
        
        if len(gauge_df) == 0:
            logger.warning("no_gauge_data", station_id=station_id)
            continue
        
        # 2. Get catchment polygon (mock for now)
        if catchment_polygons and station_id in catchment_polygons:
            catchment = catchment_polygons[station_id]
        else:
            # Mock catchment centered on Assam
            catchment = {
                "type": "Polygon",
                "coordinates": [[
                    [91.5, 26.0],
                    [91.6, 26.0],
                    [91.6, 26.1],
                    [91.5, 26.1],
                    [91.5, 26.0]
                ]]
            }
        
        # 3. Fetch weather data
        try:
            weather_df = fetch_historical_weather(
                catchment,
                start_date.date(),
                end_date.date(),
                variables=['precipitation', 'temperature_2m']
            )
        except Exception as e:
            logger.error("weather_fetch_failed", station_id=station_id, error=str(e))
            continue
        
        # Rename precipitation to rainfall_mm for consistency
        weather_df = weather_df.rename(columns={'precipitation': 'rainfall_mm'})
        
        # 4. Extract terrain features
        terrain_features = extract_terrain_features(catchment)
        
        # 5. Join weather and gauge data on timestamp
        # Ensure timestamps are aligned
        gauge_df['timestamp'] = pd.to_datetime(gauge_df['timestamp'])
        weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
        
        # Merge on timestamp (inner join to ensure alignment)
        merged = pd.merge(
            gauge_df,
            weather_df,
            on='timestamp',
            how='inner'
        )
        
        if len(merged) == 0:
            logger.warning("no_overlap_after_join", station_id=station_id)
            continue
        
        # 6. Add terrain features (static, broadcast to all rows)
        for feature_name, feature_value in terrain_features.items():
            merged[feature_name] = feature_value
        
        all_station_data.append(merged)
        
        logger.info(
            "station_processed",
            station_id=station_id,
            rows=len(merged),
            date_range=f"{merged['timestamp'].min()} to {merged['timestamp'].max()}"
        )
    
    if not all_station_data:
        logger.error("no_data_for_any_station")
        return pd.DataFrame()
    
    # Concatenate all stations
    final_df = pd.concat(all_station_data, ignore_index=True)
    
    # Sort by station and timestamp
    final_df = final_df.sort_values(['station_id', 'timestamp']).reset_index(drop=True)
    
    # Filter to good quality data only
    good_quality = final_df['quality_flag'] == 'good'
    if not good_quality.all():
        removed_count = (~good_quality).sum()
        logger.info("filtered_quality", removed_rows=int(removed_count))
        final_df = final_df[good_quality].reset_index(drop=True)
    
    logger.info(
        "dataset_complete",
        total_rows=len(final_df),
        num_stations=final_df['station_id'].nunique(),
        features=list(final_df.columns)
    )
    
    return final_df


def save_dataset(df: pd.DataFrame, filepath: str) -> None:
    """
    Save dataset to CSV for later use.
    
    Args:
        df: Dataset DataFrame
        filepath: Path to save CSV
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info("dataset_saved", filepath=filepath, rows=len(df))


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load dataset from CSV.
    
    Args:
        filepath: Path to CSV file
    
    Returns:
        Dataset DataFrame
    """
    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    logger.info("dataset_loaded", filepath=filepath, rows=len(df))
    return df
