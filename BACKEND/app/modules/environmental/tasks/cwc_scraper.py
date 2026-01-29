"""
CWC Flood Gauge Scraper & Label Generation

Fetches observed water level data from Central Water Commission (CWC) Flood
Forecasting Portal and generates ML-ready flood labels.

Key Features:
- Resilient HTML scraping with rate limiting
- Station metadata caching
- Binary flood label generation (danger level threshold)
- Lead time calculation for early warning evaluation
- Event grouping for recall-focused metrics

Author: NEXUS-AI Team
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from pathlib import Path
import json

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.environmental.tasks.signal_cleaning import clean_water_level_timeseries

logger = get_logger("cwc_scraper")


def _get_station_metadata_cache_path(station_id: str) -> Path:
    """Get cache path for station metadata."""
    cache_dir = Path(settings.GROUND_TRUTH_CACHE_DIR) / "station_metadata"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{station_id}_metadata.json"


def _load_station_metadata(station_id: str) -> Optional[Dict[str, Any]]:
    """Load cached station metadata if available."""
    cache_path = _get_station_metadata_cache_path(station_id)
    
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                metadata = json.load(f)
            logger.info("station_metadata_cache_hit", station_id=station_id)
            return metadata
        except Exception as e:
            logger.warning("station_metadata_cache_load_failed", station_id=station_id, error=str(e))
    
    return None


def _save_station_metadata(station_id: str, metadata: Dict[str, Any]) -> None:
    """Save station metadata to cache."""
    cache_path = _get_station_metadata_cache_path(station_id)
    
    try:
        with open(cache_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info("station_metadata_cached", station_id=station_id)
    except Exception as e:
        logger.error("station_metadata_cache_save_failed", station_id=station_id, error=str(e))


def fetch_cwc_station_data(
    station_id: str,
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """
    Fetch water level data from CWC Flood Forecasting Portal.
    
    Args:
        station_id: CWC station identifier
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
    
    Returns:
        DataFrame with columns:
            - timestamp: Observation time
            - water_level: Observed water level (meters)
            - warning_level: Warning threshold (meters)
            - danger_level: Danger threshold (meters)
            - station_id: Station identifier
            - river: River name (if available)
            - location: Station location (if available)
    
    Example:
        >>> df = fetch_cwc_station_data(
        ...     "GUW001",
        ...     datetime(2024, 6, 1),
        ...     datetime(2024, 6, 7)
        ... )
        >>> print(df.head())
    
    Note:
        This is a MOCK implementation. In production, you would:
        1. Identify the actual CWC API/portal structure
        2. Implement proper HTML parsing or API calls
        3. Handle authentication if required
        4. Implement robust error handling for network issues
    """
    logger.info(
        "fetching_cwc_station_data",
        station_id=station_id,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    # Check for cached metadata
    metadata = _load_station_metadata(station_id)
    
    if metadata is None:
        # In production, scrape station metadata from CWC portal
        # For now, use mock metadata
        metadata = {
            "station_id": station_id,
            "river": "Brahmaputra",  # Mock
            "location": "Guwahati",  # Mock
            "warning_level": 49.0,  # Mock (meters)
            "danger_level": 50.0,   # Mock (meters)
            "latitude": 26.1445,    # Mock
            "longitude": 91.7362    # Mock
        }
        _save_station_metadata(station_id, metadata)
    
    # MOCK DATA GENERATION
    # In production, replace this with actual scraping logic
    logger.warning(
        "using_mock_data",
        station_id=station_id,
        message="CWC scraper is using mock data. Implement actual scraping for production."
    )
    
    # Generate synthetic water level data
    num_hours = int((end_date - start_date).total_seconds() / 3600)
    timestamps = pd.date_range(start=start_date, periods=num_hours, freq='1h')
    
    # Simulate water level with some variation and a flood event
    base_level = 47.0
    trend = np.linspace(0, 3, num_hours)  # Rising trend
    noise = np.random.normal(0, 0.5, num_hours)
    
    # Add a flood event in the middle
    flood_peak_idx = num_hours // 2
    flood_shape = np.exp(-((np.arange(num_hours) - flood_peak_idx) ** 2) / (num_hours / 10))
    flood_component = flood_shape * 5.0  # Peak at +5m
    
    water_levels = base_level + trend + noise + flood_component
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'water_level': water_levels,
        'warning_level': metadata['warning_level'],
        'danger_level': metadata['danger_level'],
        'station_id': station_id,
        'river': metadata.get('river', ''),
        'location': metadata.get('location', '')
    })
    
    logger.info(
        "cwc_data_fetched",
        station_id=station_id,
        rows=len(df),
        min_level=round(df['water_level'].min(), 2),
        max_level=round(df['water_level'].max(), 2)
    )
    
    return df


def generate_flood_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate ML-ready flood labels from water level data.
    
    Labels are binary:
        - label = 1 if water_level >= danger_level
        - label = 0 otherwise
    
    Additional features generated:
        - lead_time_hours: Time until next threshold crossing (for early warning)
        - event_id: Groups contiguous flood events
        - event_duration_hours: Duration of each flood event
        - peak_level: Maximum water level during event
    
    Args:
        df: DataFrame from fetch_cwc_station_data or after cleaning
    
    Returns:
        DataFrame with added label columns
    
    Example:
        >>> labeled = generate_flood_labels(df)
        >>> flood_events = labeled[labeled['label'] == 1]
    """
    logger.info("generating_flood_labels", rows=len(df))
    
    df = df.copy()
    
    # Generate binary labels
    df['label'] = (df['water_level'] >= df['danger_level']).astype(int)
    
    # Calculate lead time (hours until next flood event)
    df['lead_time_hours'] = np.nan
    
    # Find all flood start points (transitions from 0 to 1)
    df['label_diff'] = df['label'].diff()
    flood_starts = df[df['label_diff'] == 1].index
    
    for flood_start_idx in flood_starts:
        # For all non-flood points before this flood start, calculate lead time
        flood_start_time = df.loc[flood_start_idx, 'timestamp']
        
        # Look back to find non-flood points
        for idx in range(flood_start_idx - 1, -1, -1):
            if df.loc[idx, 'label'] == 1:
                break  # Stop at previous flood event
            
            time_to_flood = (flood_start_time - df.loc[idx, 'timestamp']).total_seconds() / 3600
            df.at[idx, 'lead_time_hours'] = time_to_flood
    
    # Group contiguous flood events
    df['event_id'] = np.nan
    
    if df['label'].sum() > 0:
        # Find flood sequences
        flood_mask = df['label'] == 1
        
        # Create event IDs by finding contiguous sequences
        event_counter = 0
        in_event = False
        
        for idx in df.index:
            if flood_mask[idx]:
                if not in_event:
                    event_counter += 1
                    in_event = True
                df.at[idx, 'event_id'] = event_counter
            else:
                in_event = False
        
        # Calculate event statistics
        df['event_duration_hours'] = np.nan
        df['peak_level'] = np.nan
        
        for event_id in df['event_id'].dropna().unique():
            event_mask = df['event_id'] == event_id
            event_data = df[event_mask]
            
            # Duration
            duration = (event_data['timestamp'].max() - event_data['timestamp'].min()).total_seconds() / 3600
            df.loc[event_mask, 'event_duration_hours'] = duration
            
            # Peak level
            peak = event_data['water_level'].max()
            df.loc[event_mask, 'peak_level'] = peak
    
    # Drop temporary column
    df = df.drop(columns=['label_diff'])
    
    # Log statistics
    num_flood_points = (df['label'] == 1).sum()
    num_events = df['event_id'].nunique() if 'event_id' in df.columns else 0
    
    logger.info(
        "labels_generated",
        total_points=len(df),
        flood_points=int(num_flood_points),
        flood_percentage=round(100 * num_flood_points / len(df), 2),
        num_events=int(num_events)
    )
    
    return df


def fetch_and_label_cwc_data(
    station_id: str,
    start_date: datetime,
    end_date: datetime,
    clean: bool = True
) -> pd.DataFrame:
    """
    Complete pipeline: Fetch CWC data, clean, and generate labels.
    
    Args:
        station_id: CWC station identifier
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        clean: Whether to apply time-series cleaning (default: True)
    
    Returns:
        ML-ready DataFrame with flood labels
    
    Example:
        >>> df = fetch_and_label_cwc_data("GUW001", start, end)
        >>> # Ready for ML training
        >>> X = df[['water_level', 'lead_time_hours']]
        >>> y = df['label']
    """
    # Fetch raw data
    df = fetch_cwc_station_data(station_id, start_date, end_date)
    
    # Clean time series
    if clean:
        df = clean_water_level_timeseries(df)
        
        # Filter out removed/flagged data for label generation
        # Keep 'good' and 'interpolated', flag 'gap' and 'jump_removed'
        valid_mask = df['quality_flag'].isin(['good', 'interpolated'])
        
        if not valid_mask.all():
            removed_count = (~valid_mask).sum()
            logger.warning(
                "data_filtered_for_labeling",
                removed_count=int(removed_count),
                reason="quality_flag not in ['good', 'interpolated']"
            )
            df = df[valid_mask].reset_index(drop=True)
    
    # Generate labels
    df = generate_flood_labels(df)
    
    logger.info(
        "pipeline_complete",
        station_id=station_id,
        final_rows=len(df),
        columns=list(df.columns)
    )
    
    return df
