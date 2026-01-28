"""
Mock Landslide Inventory Generator

Generates synthetic landslide events for testing Task 9B pipeline.
Events are terrain-based (high slope) and rainfall-triggered (monsoon).

Author: NEXUS-AI Team
"""

from typing import List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger("mock_landslide_inventory")


def generate_mock_landslide_inventory(
    bbox: Tuple[float, float, float, float],
    start_date: datetime,
    end_date: datetime,
    num_events: int = 100,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic landslide inventory with realistic spatial-temporal patterns.
    
    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        start_date: Start of event period
        end_date: End of event period
        num_events: Number of landslide events to generate
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with columns: landslide_id, lat, lon, date, magnitude
    
    Example:
        >>> bbox = (89.0, 24.0, 96.0, 28.0)  # Assam region
        >>> inventory = generate_mock_landslide_inventory(bbox, start, end)
    """
    np.random.seed(seed)
    
    logger.info(
        "generating_mock_landslides",
        bbox=bbox,
        start_date=str(start_date),
        end_date=str(end_date),
        num_events=num_events
    )
    
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # Generate events with realistic patterns
    events = []
    
    # Create spatial clusters (landslides occur in groups)
    num_clusters = max(3, num_events // 20)
    cluster_centers = [
        (
            np.random.uniform(min_lon, max_lon),
            np.random.uniform(min_lat, max_lat)
        )
        for _ in range(num_clusters)
    ]
    
    for i in range(num_events):
        # Assign to a random cluster
        cluster_idx = np.random.randint(0, num_clusters)
        center_lon, center_lat = cluster_centers[cluster_idx]
        
        # Add scatter around cluster center (±0.1 degrees ≈ 10km)
        lon = center_lon + np.random.normal(0, 0.1)
        lat = center_lat + np.random.normal(0, 0.05)
        
        # Clip to bbox
        lon = np.clip(lon, min_lon, max_lon)
        lat = np.clip(lat, min_lat, max_lat)
        
        # Generate date (concentrated in monsoon: Jun-Sep)
        days_range = (end_date - start_date).days
        
        # Bias towards monsoon months (Jun=6, Sep=9)
        # Use beta distribution to concentrate events in middle of period
        date_offset = int(np.random.beta(2, 2) * days_range)
        event_date = start_date + timedelta(days=date_offset)
        
        # Further bias: 70% in monsoon months
        month = event_date.month
        if np.random.random() > 0.7 and month not in [6, 7, 8, 9]:
            # Re-sample to monsoon
            monsoon_start = datetime(event_date.year, 6, 1)
            monsoon_end = datetime(event_date.year, 9, 30)
            monsoon_days = (monsoon_end - monsoon_start).days
            monsoon_offset = np.random.randint(0, monsoon_days)
            event_date = monsoon_start + timedelta(days=monsoon_offset)
        
        # Magnitude: small (1), medium (2), large (3)
        magnitude = np.random.choice([1, 2, 3], p=[0.7, 0.25, 0.05])
        
        events.append({
            'landslide_id': f'LS_{i:04d}',
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'date': event_date.strftime('%Y-%m-%d'),
            'magnitude': magnitude,
            'type': 'rainfall-triggered'
        })
    
    df = pd.DataFrame(events)
    df = df.sort_values('date').reset_index(drop=True)
    
    logger.info(
        "mock_landslides_generated",
        total_events=len(df),
        date_range=f"{df['date'].min()} to {df['date'].max()}",
        spatial_extent=f"lon: {df['lon'].min():.2f}-{df['lon'].max():.2f}, lat: {df['lat'].min():.2f}-{df['lat'].max():.2f}"
    )
    
    # Log monthly distribution
    df_temp = df.copy()
    df_temp['month'] = pd.to_datetime(df_temp['date']).dt.month
    monthly_counts = df_temp.groupby('month').size().to_dict()
    logger.info("monthly_distribution", counts=monthly_counts)
    
    return df


def save_mock_inventory(
    df: pd.DataFrame,
    output_path: str = "data/landslide_inventory_mock.csv"
) -> None:
    """
    Save mock inventory to CSV.
    
    Args:
        df: Landslide inventory DataFrame
        output_path: Path to save CSV
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    logger.info("inventory_saved", path=str(output_file), events=len(df))


def load_landslide_inventory(
    filepath: str
) -> pd.DataFrame:
    """
    Load landslide inventory from CSV.
    
    Args:
        filepath: Path to inventory CSV
    
    Returns:
        DataFrame with standardized schema
    
    Required columns: lat, lon, date
    Optional: landslide_id, magnitude, type
    """
    logger.info("loading_inventory", path=filepath)
    
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Inventory file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Validate required columns
    required = ['lat', 'lon', 'date']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Parse date
    df['date'] = pd.to_datetime(df['date'])
    
    logger.info(
        "inventory_loaded",
        events=len(df),
        date_range=f"{df['date'].min()} to {df['date'].max()}"
    )
    
    return df
