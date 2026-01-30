"""
Weather ETL Pipeline for Catchment-Level Rainfall Aggregation

Fetches historical and forecast weather data from Open-Meteo API,
aggregates rainfall over catchment polygons, and produces ML-ready time series.

Supports both flood forecasting and landslide triggering models.

Key Features:
- Historical data: ERA5 reanalysis (1940-present)
- Forecast data: GFS/ICON models (7-day horizon)
- Smart catchment sampling (1-9 points based on area)
- Mean Areal Precipitation (MAP) computation
- Time-series sanitization (gap filling, interpolation)
- File-based caching for performance

Author: NEXUS-AI Team
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import time
import numpy as np
import pandas as pd
import requests
from shapely.geometry import shape, Point, Polygon
from shapely.ops import unary_union

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.environmental.utils.weather_cache import (
    generate_cache_key,
    load_from_cache,
    save_to_cache
)

logger = get_logger("weather_etl")


def _generate_sampling_points(catchment_polygon: Dict[str, Any]) -> List[Tuple[float, float]]:
    """
    Generate representative sampling points for catchment.
    
    Strategy based on catchment area:
    - Small (< 100 km²): 1 point (centroid)
    - Medium (100-1000 km²): 5 points (centroid + 4 corners)
    - Large (> 1000 km²): 9 points (3x3 grid)
    
    Args:
        catchment_polygon: GeoJSON polygon dict
    
    Returns:
        List of (lat, lon) tuples
    """
    geom = shape(catchment_polygon)
    
    # Calculate area in km² using geodesic calculation
    # For better accuracy, we use a rough conversion based on latitude
    # At equator: 1 degree ≈ 111 km
    # Area correction factor varies with latitude
    minx, miny, maxx, maxy = geom.bounds
    avg_lat = (miny + maxy) / 2
    
    # Latitude correction: 1 degree longitude = 111 * cos(lat) km
    import math
    lat_correction = math.cos(math.radians(avg_lat))
    
    # Calculate area in km²
    area_deg2 = geom.area
    # area = width_km * height_km
    # width_km = (maxx - minx) * 111 * cos(lat)
    # height_km = (maxy - miny) * 111
    area_km2 = area_deg2 * (111 ** 2) * lat_correction
    
    # Get bounding box
    # Centroid (always included)
    centroid = geom.centroid
    points = [(centroid.y, centroid.x)]  # (lat, lon)
    
    if area_km2 < 100:
        # Small catchment: centroid only
        logger.info("sampling_strategy", area_km2=round(area_km2, 2), num_points=1, strategy="centroid")
        return points
    
    elif area_km2 < 1000:
        # Medium catchment: centroid + 4 corners
        corners = [
            (miny, minx),  # SW
            (miny, maxx),  # SE
            (maxy, minx),  # NW
            (maxy, maxx),  # NE
        ]
        
        # Only include corners that are inside the polygon
        for lat, lon in corners:
            pt = Point(lon, lat)
            if geom.contains(pt) or geom.touches(pt):
                points.append((lat, lon))
        
        logger.info("sampling_strategy", area_km2=round(area_km2, 2), num_points=len(points), strategy="5-point")
        return points
    
    else:
        # Large catchment: 3x3 grid
        lat_step = (maxy - miny) / 3
        lon_step = (maxx - minx) / 3
        
        for i in range(3):
            for j in range(3):
                lat = miny + (i + 0.5) * lat_step
                lon = minx + (j + 0.5) * lon_step
                pt = Point(lon, lat)
                
                if geom.contains(pt) or geom.touches(pt):
                    points.append((lat, lon))
        
        logger.info("sampling_strategy", area_km2=round(area_km2, 2), num_points=len(points), strategy="9-point")
        return points


def _fetch_weather_api(
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    variables: List[str],
    is_forecast: bool = False
) -> Optional[pd.DataFrame]:
    """
    Fetch weather data from Open-Meteo API for a single point.
    
    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start date
        end_date: End date
        variables: List of variables (e.g., ['precipitation', 'temperature_2m'])
        is_forecast: If True, use forecast API; otherwise historical
    
    Returns:
        DataFrame with columns: timestamp, variable1, variable2, ...
    """
    # Select API endpoint
    if is_forecast:
        base_url = f"{settings.OPEN_METEO_BASE_URL}/forecast"
        forecast_days = (end_date - start_date).days + 1
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(variables),
            "forecast_days": min(forecast_days, 16),  # Max 16 days for free tier
            "timezone": "UTC"
        }
    else:
        base_url = f"{settings.OPEN_METEO_ARCHIVE_URL}/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": ",".join(variables),
            "timezone": "UTC"
        }
    
    # Retry logic with exponential backoff
    for attempt in range(1, settings.WEATHER_MAX_RETRIES + 1):
        try:
            logger.info(
                "api_request",
                attempt=attempt,
                lat=lat,
                lon=lon,
                start_date=str(start_date),
                end_date=str(end_date),
                is_forecast=is_forecast
            )
            
            response = requests.get(
                base_url,
                params=params,
                timeout=settings.WEATHER_API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse response
                hourly = data.get("hourly", {})
                timestamps = hourly.get("time", [])
                
                if not timestamps:
                    logger.warning("no_data_returned", lat=lat, lon=lon)
                    return None
                
                # Build DataFrame
                df_data = {"timestamp": pd.to_datetime(timestamps)}
                
                for var in variables:
                    values = hourly.get(var, [])
                    df_data[var] = values
                
                df = pd.DataFrame(df_data)
                
                logger.info(
                    "api_success",
                    lat=lat,
                    lon=lon,
                    rows=len(df),
                    variables=variables
                )
                
                return df
            
            elif response.status_code == 429:
                # Rate limit hit
                wait_time = settings.WEATHER_RETRY_DELAY ** attempt
                logger.warning("rate_limit_hit", attempt=attempt, wait_seconds=wait_time)
                time.sleep(wait_time)
                continue
            
            else:
                logger.error(
                    "api_error",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                
                if attempt < settings.WEATHER_MAX_RETRIES:
                    time.sleep(settings.WEATHER_RETRY_DELAY ** attempt)
                    continue
                else:
                    return None
        
        except requests.exceptions.Timeout:
            logger.warning("request_timeout", attempt=attempt)
            if attempt < settings.WEATHER_MAX_RETRIES:
                time.sleep(settings.WEATHER_RETRY_DELAY ** attempt)
                continue
            else:
                return None
        
        except Exception as e:
            logger.error("request_exception", attempt=attempt, error=str(e))
            if attempt < settings.WEATHER_MAX_RETRIES:
                time.sleep(settings.WEATHER_RETRY_DELAY ** attempt)
                continue
            else:
                return None
    
    return None


def fetch_historical_weather(
    catchment_polygon: Dict[str, Any],
    start_date: date,
    end_date: date,
    variables: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Fetch historical weather data for catchment from Open-Meteo (ERA5).
    
    Args:
        catchment_polygon: GeoJSON polygon dict
        start_date: Start date for data
        end_date: End date for data
        variables: List of variables (default: ['precipitation'])
    
    Returns:
        DataFrame with columns: timestamp, variable1, variable2, ...
        Aggregated over catchment using Mean Areal Precipitation
    
    Example:
        >>> catchment = {"type": "Polygon", "coordinates": [...]}
        >>> df = fetch_historical_weather(
        ...     catchment,
        ...     date(2024, 1, 1),
        ...     date(2024, 1, 7),
        ...     variables=['precipitation', 'temperature_2m']
        ... )
        >>> print(df.head())
    """
    if variables is None:
        variables = ['precipitation']
    
    logger.info(
        "fetch_historical_weather",
        start_date=str(start_date),
        end_date=str(end_date),
        variables=variables
    )
    
    # Check cache
    cache_key = generate_cache_key(
        catchment_polygon,
        start_date,
        end_date,
        variables,
        data_type="historical"
    )
    
    cached_data = load_from_cache(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Generate sampling points
    sampling_points = _generate_sampling_points(catchment_polygon)
    
    # Fetch data for each point
    point_dataframes = []
    
    for lat, lon in sampling_points:
        df = _fetch_weather_api(lat, lon, start_date, end_date, variables, is_forecast=False)
        
        if df is not None:
            point_dataframes.append(df)
    
    if not point_dataframes:
        logger.error("no_data_fetched", num_points=len(sampling_points))
        raise RuntimeError("Failed to fetch weather data from any sampling point")
    
    # Aggregate across points (simple mean)
    # Align all dataframes on timestamp
    merged = point_dataframes[0].copy()
    
    for i, df in enumerate(point_dataframes[1:], start=1):
        merged = merged.merge(
            df,
            on='timestamp',
            how='outer',
            suffixes=('', f'_p{i}')
        )
    
    # Compute mean for each variable
    result = pd.DataFrame({'timestamp': merged['timestamp']})
    
    for var in variables:
        # Find all columns for this variable
        var_cols = [col for col in merged.columns if col.startswith(var)]
        result[var] = merged[var_cols].mean(axis=1)
    
    # Save to cache
    save_to_cache(cache_key, result)
    
    logger.info(
        "historical_weather_fetched",
        rows=len(result),
        variables=variables,
        num_points=len(sampling_points)
    )
    
    return result


def fetch_forecast_weather(
    catchment_polygon: Dict[str, Any],
    horizon_days: int = 7,
    variables: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Fetch forecast weather data for catchment from Open-Meteo (GFS/ICON).
    
    Args:
        catchment_polygon: GeoJSON polygon dict
        horizon_days: Number of days to forecast (default: 7, max: 16)
        variables: List of variables (default: ['precipitation'])
    
    Returns:
        DataFrame with columns: timestamp, variable1, variable2, ...
        Aggregated over catchment using Mean Areal Precipitation
    
    Example:
        >>> catchment = {"type": "Polygon", "coordinates": [...]}
        >>> df = fetch_forecast_weather(catchment, horizon_days=7)
        >>> print(df.head())
    """
    if variables is None:
        variables = ['precipitation']
    
    start_date = date.today()
    end_date = start_date + timedelta(days=horizon_days - 1)
    
    logger.info(
        "fetch_forecast_weather",
        horizon_days=horizon_days,
        start_date=str(start_date),
        end_date=str(end_date),
        variables=variables
    )
    
    # Check cache (forecast cache expires quickly, so we use current date in key)
    cache_key = generate_cache_key(
        catchment_polygon,
        start_date,
        end_date,
        variables,
        data_type="forecast"
    )
    
    cached_data = load_from_cache(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Generate sampling points
    sampling_points = _generate_sampling_points(catchment_polygon)
    
    # Fetch data for each point
    point_dataframes = []
    
    for lat, lon in sampling_points:
        df = _fetch_weather_api(lat, lon, start_date, end_date, variables, is_forecast=True)
        
        if df is not None:
            point_dataframes.append(df)
    
    if not point_dataframes:
        logger.error("no_forecast_data_fetched", num_points=len(sampling_points))
        raise RuntimeError("Failed to fetch forecast data from any sampling point")
    
    # Aggregate across points (simple mean)
    merged = point_dataframes[0].copy()
    
    for i, df in enumerate(point_dataframes[1:], start=1):
        merged = merged.merge(
            df,
            on='timestamp',
            how='outer',
            suffixes=('', f'_p{i}')
        )
    
    # Compute mean for each variable
    result = pd.DataFrame({'timestamp': merged['timestamp']})
    
    for var in variables:
        var_cols = [col for col in merged.columns if col.startswith(var)]
        result[var] = merged[var_cols].mean(axis=1)
    
    # Save to cache
    save_to_cache(cache_key, result)
    
    logger.info(
        "forecast_weather_fetched",
        rows=len(result),
        variables=variables,
        num_points=len(sampling_points)
    )
    
    return result


def aggregate_rainfall_to_catchment(
    weather_data: pd.DataFrame,
    catchment_id: str
) -> pd.DataFrame:
    """
    Aggregate weather data to catchment level with metadata.
    
    Args:
        weather_data: DataFrame from fetch_historical_weather() or fetch_forecast_weather()
        catchment_id: Unique identifier for catchment
    
    Returns:
        DataFrame with columns: timestamp, catchment_id, rainfall_mm, [other variables]
    
    Example:
        >>> weather = fetch_historical_weather(catchment, start, end)
        >>> aggregated = aggregate_rainfall_to_catchment(weather, "catch_001")
    """
    result = weather_data.copy()
    result['catchment_id'] = catchment_id
    
    # Rename precipitation to rainfall_mm for clarity
    if 'precipitation' in result.columns:
        result['rainfall_mm'] = result['precipitation']
        result = result.drop(columns=['precipitation'])
    
    # Reorder columns
    cols = ['timestamp', 'catchment_id', 'rainfall_mm'] + [
        col for col in result.columns if col not in ['timestamp', 'catchment_id', 'rainfall_mm']
    ]
    result = result[cols]
    
    logger.info("rainfall_aggregated", catchment_id=catchment_id, rows=len(result))
    
    return result


def sanitize_timeseries(
    df: pd.DataFrame,
    max_gap_hours: int = 6
) -> pd.DataFrame:
    """
    Sanitize time series data: handle gaps, interpolate, ensure monotonic time.
    
    Args:
        df: DataFrame with 'timestamp' column
        max_gap_hours: Maximum gap to interpolate (hours)
    
    Returns:
        Sanitized DataFrame with 'quality_flag' column added
    
    Quality flags:
    - 'good': Original data
    - 'interpolated': Filled via interpolation
    - 'gap': Long gap detected (not filled)
    """
    logger.info("sanitizing_timeseries", rows=len(df))
    
    df = df.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Remove duplicates
    duplicates = df.duplicated(subset=['timestamp'], keep='first')
    if duplicates.any():
        num_duplicates = duplicates.sum()
        logger.warning("duplicates_removed", count=num_duplicates)
        df = df[~duplicates].reset_index(drop=True)
    
    # Add quality flag
    df['quality_flag'] = 'good'
    
    # Detect gaps
    df['time_diff'] = df['timestamp'].diff()
    
    # Find gaps larger than expected (assuming hourly data)
    expected_interval = pd.Timedelta(hours=1)
    max_gap = pd.Timedelta(hours=max_gap_hours)
    
    gaps = df['time_diff'] > expected_interval * 1.5  # Allow 50% tolerance
    
    if gaps.any():
        num_gaps = gaps.sum()
        logger.info("gaps_detected", count=num_gaps)
        
        interpolated_rows = []
        
        # Iterate over gaps
        for idx in df[gaps].index:
            gap_size = df.loc[idx, 'time_diff']
            
            if gap_size <= max_gap:
                # Interpolate short gaps
                prev_idx = idx - 1
                
                # Create missing timestamps
                start_time = df.loc[prev_idx, 'timestamp']
                end_time = df.loc[idx, 'timestamp']
                
                missing_times = pd.date_range(
                    start=start_time + expected_interval,
                    end=end_time - expected_interval,
                    freq='1h'
                )
                
                if len(missing_times) > 0:
                    logger.info("gap_interpolated", gap_hours=gap_size.total_seconds() / 3600)
                    
                    for ts in missing_times:
                        row = {'timestamp': ts, 'quality_flag': 'interpolated'}
                        
                        # Linear interpolation for numeric columns
                        for col in df.columns:
                            if col not in ['timestamp', 'time_diff', 'quality_flag'] and pd.api.types.is_numeric_dtype(df[col]):
                                prev_val = df.loc[prev_idx, col]
                                next_val = df.loc[idx, col]
                                
                                if pd.notna(prev_val) and pd.notna(next_val):
                                    # Linear interpolation
                                    total_gap = (end_time - start_time).total_seconds()
                                    current_gap = (ts - start_time).total_seconds()
                                    weight = current_gap / total_gap
                                    
                                    row[col] = prev_val + weight * (next_val - prev_val)
                                else:
                                    row[col] = np.nan
                            elif col not in ['timestamp', 'time_diff', 'quality_flag']:
                                # Copy non-numeric values from previous row
                                row[col] = df.loc[prev_idx, col]
                        
                        interpolated_rows.append(row)
            else:
                # Long gap - flag but don't interpolate
                # Just mark the AFTER gap row as start of new segment or just flag it
                # We flag the row at 'idx' which represents the first point AFTER the gap
                df.at[idx, 'quality_flag'] = 'gap'
                logger.warning("long_gap_detected", gap_hours=gap_size.total_seconds() / 3600)
        
        # Add all interpolated rows at once
        if interpolated_rows:
            df = pd.concat([df, pd.DataFrame(interpolated_rows)], ignore_index=True)
            df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Drop time_diff column
    df = df.drop(columns=['time_diff'])
    
    # Final validation
    assert df['timestamp'].is_monotonic_increasing, "Timestamp not monotonic after sanitization"
    
    logger.info("timeseries_sanitized", final_rows=len(df))
    
    return df
