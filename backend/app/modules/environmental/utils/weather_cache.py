"""
Weather data caching utilities for Open-Meteo API responses.

Implements file-based caching to avoid redundant API calls and improve performance.
Cache keys are deterministic based on catchment geometry and date range.

Author: NEXUS-AI Team
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, date
import pandas as pd

from shapely.geometry import shape, mapping
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("weather_cache")


def generate_cache_key(
    catchment_polygon: Dict[str, Any],
    start_date: date,
    end_date: date,
    variables: list,
    data_type: str = "historical"
) -> str:
    """
    Generate deterministic cache key from request parameters.
    
    Args:
        catchment_polygon: GeoJSON polygon dict
        start_date: Start date for data
        end_date: End date for data
        variables: List of weather variables
        data_type: "historical" or "forecast"
    
    Returns:
        16-character hash string
    """
    # Create deterministic string from inputs
    # Use WKT for geometry to ensure consistent ordering
    geom = shape(catchment_polygon)
    wkt = geom.wkt
    
    # Sort variables for consistency
    vars_str = ",".join(sorted(variables))
    
    key_string = f"{data_type}_{wkt}_{start_date.isoformat()}_{end_date.isoformat()}_{vars_str}"
    
    # Generate SHA256 hash and truncate
    hash_obj = hashlib.sha256(key_string.encode())
    return hash_obj.hexdigest()[:16]


def get_cache_path(cache_key: str) -> Path:
    """
    Get cache file path for given cache key.
    
    Args:
        cache_key: Cache key from generate_cache_key()
    
    Returns:
        Path to cache file (parquet format)
    """
    cache_dir = Path(settings.WEATHER_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir / f"weather_{cache_key}.parquet"


def load_from_cache(cache_key: str) -> Optional[pd.DataFrame]:
    """
    Load weather data from cache if it exists.
    
    Args:
        cache_key: Cache key from generate_cache_key()
    
    Returns:
        DataFrame if cache hit, None if cache miss
    """
    cache_path = get_cache_path(cache_key)
    
    if not cache_path.exists():
        logger.info("cache_miss", cache_key=cache_key)
        return None
    
    try:
        df = pd.read_parquet(cache_path)
        logger.info("cache_hit", cache_key=cache_key, rows=len(df))
        return df
    except Exception as e:
        logger.warning("cache_load_failed", cache_key=cache_key, error=str(e))
        return None


def save_to_cache(cache_key: str, data: pd.DataFrame) -> None:
    """
    Save weather data to cache.
    
    Args:
        cache_key: Cache key from generate_cache_key()
        data: DataFrame to cache
    """
    cache_path = get_cache_path(cache_key)
    
    try:
        # Save as parquet for efficient storage and fast loading
        data.to_parquet(cache_path, compression='snappy', index=False)
        
        file_size_kb = cache_path.stat().st_size / 1024
        logger.info(
            "cache_saved",
            cache_key=cache_key,
            rows=len(data),
            size_kb=round(file_size_kb, 2)
        )
    except Exception as e:
        logger.error("cache_save_failed", cache_key=cache_key, error=str(e))


def clear_cache(older_than_days: Optional[int] = None) -> int:
    """
    Clear weather cache files.
    
    Args:
        older_than_days: If specified, only delete files older than this many days
    
    Returns:
        Number of files deleted
    """
    cache_dir = Path(settings.WEATHER_CACHE_DIR)
    
    if not cache_dir.exists():
        return 0
    
    deleted = 0
    cutoff_time = None
    
    if older_than_days is not None:
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
    
    for cache_file in cache_dir.glob("weather_*.parquet"):
        try:
            if cutoff_time is not None:
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_mtime > cutoff_time:
                    continue
            
            cache_file.unlink()
            deleted += 1
        except Exception as e:
            logger.warning("cache_delete_failed", file=str(cache_file), error=str(e))
    
    logger.info("cache_cleared", files_deleted=deleted)
    return deleted
