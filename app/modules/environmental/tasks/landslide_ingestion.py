"""
Landslide Inventory Ingestion

Normalizes landslide event data from multiple sources into a standardized format.
This module ONLY handles ingestion - landslide ML models are not part of Task 8.

Supported Sources:
- NASA Global Landslide Catalog (GLC)
- State/District custom CSV inventories

Output Schema:
    timestamp | lat | lon | event_type | source | location_name | fatalities (optional)

Author: NEXUS-AI Team
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import requests

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("landslide_ingestion")


# India bounding box for coordinate validation
INDIA_BBOX = {
    'min_lat': 6.0,
    'max_lat': 37.0,
    'min_lon': 68.0,
    'max_lon': 98.0
}


def _validate_coordinates(lat: float, lon: float, region_bbox: Optional[Dict] = None) -> bool:
    """
    Validate that coordinates are within expected region.
    
    Args:
        lat: Latitude
        lon: Longitude
        region_bbox: Optional custom bounding box (default: India)
    
    Returns:
        True if coordinates are valid
    """
    if region_bbox is None:
        region_bbox = INDIA_BBOX
    
    return (
        region_bbox['min_lat'] <= lat <= region_bbox['max_lat'] and
        region_bbox['min_lon'] <= lon <= region_bbox['max_lon']
    )


def _parse_date_robust(date_str: Any) -> Optional[datetime]:
    """
    Robustly parse date strings in multiple formats.
    
    Args:
        date_str: Date string or datetime object
    
    Returns:
        Parsed datetime or None if parsing fails
    """
    if pd.isna(date_str):
        return None
    
    if isinstance(date_str, datetime):
        return date_str
    
    if isinstance(date_str, pd.Timestamp):
        return date_str.to_pydatetime()
    
    # Try multiple date formats
    date_formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%m/%d/%Y',
        '%m-%d-%Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue
    
    # Try pandas parsing as last resort
    try:
        return pd.to_datetime(date_str)
    except:
        logger.warning("date_parse_failed", date_str=str(date_str))
        return None


def ingest_nasa_glc(filepath_or_url: str) -> pd.DataFrame:
    """
    Ingest NASA Global Landslide Catalog.
    
    Args:
        filepath_or_url: Path to CSV file or URL to NASA GLC data
    
    Returns:
        Normalized DataFrame with standardized schema
    
    Example:
        >>> df = ingest_nasa_glc("https://data.nasa.gov/.../landslides.csv")
        >>> india_landslides = df[df['source'] == 'NASA_GLC']
    
    Note:
        NASA GLC schema (typical columns):
        - event_date: Date of landslide
        - latitude, longitude: Coordinates
        - landslide_category: Type (e.g., landslide, mudslide, debris flow)
        - fatality_count: Number of fatalities
        - location_description: Text description
    """
    logger.info("ingesting_nasa_glc", source=filepath_or_url)
    
    # Load data
    if filepath_or_url.startswith('http'):
        try:
            df = pd.read_csv(filepath_or_url)
            logger.info("nasa_glc_downloaded", rows=len(df))
        except Exception as e:
            logger.error("nasa_glc_download_failed", error=str(e))
            return pd.DataFrame(columns=['timestamp', 'lat', 'lon', 'event_type', 'source', 'location_name'])
    else:
        try:
            df = pd.read_csv(filepath_or_url)
            logger.info("nasa_glc_loaded", rows=len(df))
        except Exception as e:
            logger.error("nasa_glc_load_failed", error=str(e))
            return pd.DataFrame(columns=['timestamp', 'lat', 'lon', 'event_type', 'source', 'location_name'])
    
    # Map NASA GLC columns to standardized schema
    # Note: Actual column names may vary - adjust based on real NASA GLC format
    column_mapping = {
        'event_date': 'timestamp',
        'latitude': 'lat',
        'longitude': 'lon',
        'landslide_category': 'event_type',
        'location_description': 'location_name',
        'fatality_count': 'fatalities'
    }
    
    # Rename columns that exist
    rename_dict = {old: new for old, new in column_mapping.items() if old in df.columns}
    df = df.rename(columns=rename_dict)
    
    # Ensure required columns exist
    required_cols = ['timestamp', 'lat', 'lon']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error("nasa_glc_missing_columns", missing=missing_cols)
        return pd.DataFrame(columns=['timestamp', 'lat', 'lon', 'event_type', 'source', 'location_name'])
    
    # Add source column
    df['source'] = 'NASA_GLC'
    
    # Parse timestamps
    df['timestamp'] = df['timestamp'].apply(_parse_date_robust)
    
    # Validate coordinates
    valid_coords = df.apply(
        lambda row: _validate_coordinates(row['lat'], row['lon']) if pd.notna(row['lat']) and pd.notna(row['lon']) else False,
        axis=1
    )
    
    invalid_count = (~valid_coords).sum()
    if invalid_count > 0:
        logger.warning("invalid_coordinates_filtered", count=int(invalid_count))
        df = df[valid_coords].reset_index(drop=True)
    
    # Filter out rows with missing timestamps or coordinates
    complete_mask = df['timestamp'].notna() & df['lat'].notna() & df['lon'].notna()
    incomplete_count = (~complete_mask).sum()
    
    if incomplete_count > 0:
        logger.warning("incomplete_records_filtered", count=int(incomplete_count))
        df = df[complete_mask].reset_index(drop=True)
    
    # Standardize event_type
    if 'event_type' not in df.columns:
        df['event_type'] = 'landslide'
    
    # Select final columns
    final_cols = ['timestamp', 'lat', 'lon', 'event_type', 'source', 'location_name']
    if 'fatalities' in df.columns:
        final_cols.append('fatalities')
    
    # Add missing optional columns
    for col in final_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    df = df[final_cols]
    
    logger.info(
        "nasa_glc_ingested",
        final_rows=len(df),
        date_range=f"{df['timestamp'].min()} to {df['timestamp'].max()}" if len(df) > 0 else "N/A"
    )
    
    return df


def ingest_custom_csv(
    filepath: str,
    schema_mapping: Dict[str, str]
) -> pd.DataFrame:
    """
    Ingest custom landslide inventory CSV with user-defined schema mapping.
    
    Args:
        filepath: Path to CSV file
        schema_mapping: Dictionary mapping CSV columns to standard schema
            Example: {
                'Date': 'timestamp',
                'Latitude': 'lat',
                'Longitude': 'lon',
                'Type': 'event_type',
                'Location': 'location_name'
            }
    
    Returns:
        Normalized DataFrame with standardized schema
    
    Example:
        >>> mapping = {'Date': 'timestamp', 'Lat': 'lat', 'Lon': 'lon'}
        >>> df = ingest_custom_csv("assam_landslides.csv", mapping)
    """
    logger.info("ingesting_custom_csv", filepath=filepath)
    
    try:
        df = pd.read_csv(filepath)
        logger.info("custom_csv_loaded", rows=len(df))
    except Exception as e:
        logger.error("custom_csv_load_failed", error=str(e))
        return pd.DataFrame(columns=['timestamp', 'lat', 'lon', 'event_type', 'source', 'location_name'])
    
    # Rename columns based on mapping
    rename_dict = {old: new for old, new in schema_mapping.items() if old in df.columns}
    df = df.rename(columns=rename_dict)
    
    # Ensure required columns exist
    required_cols = ['timestamp', 'lat', 'lon']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error("custom_csv_missing_columns", missing=missing_cols, mapping=schema_mapping)
        return pd.DataFrame(columns=['timestamp', 'lat', 'lon', 'event_type', 'source', 'location_name'])
    
    # Add source column
    source_name = Path(filepath).stem
    df['source'] = f'CUSTOM_{source_name}'
    
    # Parse timestamps
    df['timestamp'] = df['timestamp'].apply(_parse_date_robust)
    
    # Validate coordinates
    valid_coords = df.apply(
        lambda row: _validate_coordinates(row['lat'], row['lon']) if pd.notna(row['lat']) and pd.notna(row['lon']) else False,
        axis=1
    )
    
    invalid_count = (~valid_coords).sum()
    if invalid_count > 0:
        logger.warning("invalid_coordinates_filtered", count=int(invalid_count))
        df = df[valid_coords].reset_index(drop=True)
    
    # Filter out rows with missing timestamps or coordinates
    complete_mask = df['timestamp'].notna() & df['lat'].notna() & df['lon'].notna()
    incomplete_count = (~complete_mask).sum()
    
    if incomplete_count > 0:
        logger.warning("incomplete_records_filtered", count=int(incomplete_count))
        df = df[complete_mask].reset_index(drop=True)
    
    # Standardize event_type
    if 'event_type' not in df.columns:
        df['event_type'] = 'landslide'
    
    # Select final columns
    final_cols = ['timestamp', 'lat', 'lon', 'event_type', 'source', 'location_name']
    if 'fatalities' in df.columns:
        final_cols.append('fatalities')
    
    # Add missing optional columns
    for col in final_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    df = df[final_cols]
    
    logger.info(
        "custom_csv_ingested",
        final_rows=len(df),
        date_range=f"{df['timestamp'].min()} to {df['timestamp'].max()}" if len(df) > 0 else "N/A"
    )
    
    return df


def normalize_landslide_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize and validate landslide inventory data.
    
    Performs final validation and standardization:
    - Ensure datetime types
    - Validate coordinate ranges
    - Sort by timestamp
    - Remove duplicates
    
    Args:
        df: DataFrame from ingest_nasa_glc or ingest_custom_csv
    
    Returns:
        Normalized and validated DataFrame
    
    Example:
        >>> raw_df = ingest_nasa_glc(url)
        >>> clean_df = normalize_landslide_data(raw_df)
    """
    logger.info("normalizing_landslide_data", rows=len(df))
    
    df = df.copy()
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Remove rows with invalid timestamps
    invalid_ts = df['timestamp'].isna()
    if invalid_ts.any():
        logger.warning("invalid_timestamps_removed", count=int(invalid_ts.sum()))
        df = df[~invalid_ts].reset_index(drop=True)
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Remove exact duplicates
    duplicates = df.duplicated(subset=['timestamp', 'lat', 'lon'], keep='first')
    if duplicates.any():
        logger.warning("duplicates_removed", count=int(duplicates.sum()))
        df = df[~duplicates].reset_index(drop=True)
    
    # Final validation
    assert df['timestamp'].is_monotonic_increasing, "Timestamps not monotonic after normalization"
    assert (df['lat'].between(INDIA_BBOX['min_lat'], INDIA_BBOX['max_lat'])).all(), "Invalid latitudes found"
    assert (df['lon'].between(INDIA_BBOX['min_lon'], INDIA_BBOX['max_lon'])).all(), "Invalid longitudes found"
    
    logger.info(
        "normalization_complete",
        final_rows=len(df),
        date_range=f"{df['timestamp'].min()} to {df['timestamp'].max()}"
    )
    
    return df
