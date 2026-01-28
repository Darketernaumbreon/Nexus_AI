"""
Feature Builder Service

Constructs inference-time features from raw inputs.
Ensures feature consistency with training pipeline.

Latency Budget:
    - Weather fetch: <= 200ms (cached)
    - Feature build: <= 50ms
    - Total: <= 250ms

Author: NEXUS-AI Team
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("feature_builder")


class FeatureValidationError(Exception):
    """Raised when features don't match expected training features."""
    pass


def validate_features(df: pd.DataFrame, expected_features: List[str]) -> None:
    """
    Validate that DataFrame columns match expected training features.
    
    Fail fast on feature drift to prevent silent incorrect predictions.
    
    Args:
        df: Features DataFrame
        expected_features: List of expected feature names
    
    Raises:
        FeatureValidationError: If features don't match
    """
    actual_features = set(df.columns)
    expected_set = set(expected_features)
    
    if actual_features != expected_set:
        missing = expected_set - actual_features
        extra = actual_features - expected_set
        
        logger.error(
            "feature_validation_failed",
            missing=list(missing),
            extra=list(extra)
        )
        
        raise FeatureValidationError(
            f"Feature mismatch! Missing: {missing}, Extra: {extra}"
        )
    
    logger.debug("feature_validation_passed", count=len(expected_features))


def build_flood_features(
    station_id: str,
    timestamp: Optional[datetime] = None,
    expected_features: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Build flood prediction features for a given station.
    
    Latency Budget:
        - Weather fetch: <= 200ms (cached)
        - Terrain lookup: <= 20ms
        - Feature computation: <= 30ms
    
    Args:
        station_id: CWC gauge station ID
        timestamp: Prediction timestamp (default: now)
        expected_features: List of expected features for validation
    
    Returns:
        DataFrame with single row of features
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    logger.info(
        "building_flood_features",
        station_id=station_id,
        timestamp=str(timestamp)
    )
    
    # ===================================================================
    # MOCK FEATURES (Replace with real data in production)
    # In production:
    #   1. Fetch recent weather from cache/API
    #   2. Fetch terrain features from DB
    #   3. Compute lag/rolling features
    # ===================================================================
    
    # Mock terrain features (would come from station metadata)
    terrain = {
        'catchment_area': 110.5,
        'mean_hand': 5.0,
        'mean_slope': 2.5
    }
    
    # Mock weather features (would come from weather cache)
    np.random.seed(int(timestamp.timestamp()) % 1000)
    rainfall = np.random.exponential(3)  # Current rainfall
    temperature = np.random.uniform(20, 35)
    
    # Build feature dictionary
    features = {
        'rainfall_mm': rainfall,
        'temperature_2m': temperature,
        'catchment_area': terrain['catchment_area'],
        'mean_hand': terrain['mean_hand'],
        'mean_slope': terrain['mean_slope'],
        
        # Lag features (would be computed from historical data)
        'rainfall_mm_lag_1': rainfall * 0.8,
        'rainfall_mm_lag_2': rainfall * 0.6,
        'rainfall_mm_lag_3': rainfall * 0.5,
        'rainfall_mm_lag_5': rainfall * 0.3,
        'rainfall_mm_lag_7': rainfall * 0.2,
        
        'temperature_2m_lag_1': temperature - 1,
        'temperature_2m_lag_2': temperature - 2,
        'temperature_2m_lag_3': temperature - 1.5,
        'temperature_2m_lag_5': temperature - 0.5,
        'temperature_2m_lag_7': temperature + 0.5,
        
        # Rolling features
        'rainfall_mm_3d_sum': rainfall * 2.5,
        'rainfall_mm_5d_sum': rainfall * 4.0,
        'rainfall_mm_7d_sum': rainfall * 5.5
    }
    
    df = pd.DataFrame([features])
    
    # Validate features if expected list provided
    if expected_features:
        # Reorder columns to match training order
        df = df[expected_features]
        validate_features(df, expected_features)
    
    logger.info(
        "flood_features_built",
        num_features=len(df.columns),
        station_id=station_id
    )
    
    return df


def build_landslide_features(
    lat: float,
    lon: float,
    date: Optional[datetime] = None,
    expected_features: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Build landslide prediction features for a given location.
    
    Latency Budget:
        - Weather fetch: <= 200ms (cached)
        - DEM lookup: <= 30ms
        - Feature computation: <= 20ms
    
    Args:
        lat: Latitude
        lon: Longitude
        date: Prediction date (default: today)
        expected_features: List of expected features for validation
    
    Returns:
        DataFrame with single row of features
    """
    if date is None:
        date = datetime.utcnow()
    
    logger.info(
        "building_landslide_features",
        lat=lat,
        lon=lon,
        date=str(date.date())
    )
    
    # ===================================================================
    # MOCK FEATURES (Replace with real data in production)
    # In production:
    #   1. Extract slope/aspect/curvature from DEM at location
    #   2. Fetch rainfall from cache/API
    #   3. Compute ARI and interaction features
    # ===================================================================
    
    np.random.seed(int((lat + lon) * 1000) % 10000)
    
    # Mock terrain features (would come from DEM extraction)
    slope = np.random.uniform(5, 35)
    aspect = np.random.uniform(0, 360)
    curvature = np.random.normal(0, 0.02)
    elevation = np.random.uniform(100, 2000)
    
    # Mock weather features
    rainfall = np.random.exponential(3)
    temperature = np.random.uniform(18, 32)
    
    # Build feature dictionary
    features = {
        'slope': slope,
        'aspect': aspect,
        'curvature': curvature,
        'elevation': elevation,
        'rainfall_mm': rainfall,
        'temperature': temperature,
        
        # ARI features
        'rainfall_mm_ari_3d': rainfall * 2.5,
        'rainfall_mm_ari_7d': rainfall * 5.0,
        'rainfall_mm_ari_14d': rainfall * 8.0,
        'rainfall_mm_ari_30d': rainfall * 12.0,
        
        # Lag features
        'rainfall_mm_lag_1': rainfall * 0.9,
        'rainfall_mm_lag_3': rainfall * 0.7,
        'rainfall_mm_lag_7': rainfall * 0.4,
        'temperature_lag_1': temperature - 0.5,
        'temperature_lag_3': temperature - 1.0,
        'temperature_lag_7': temperature - 1.5,
        
        # Rolling features
        'rainfall_mm_3d_sum': rainfall * 2.5,
        'rainfall_mm_7d_sum': rainfall * 5.0,
        
        # Physics interactions
        'slope_rainfall_interaction': slope * rainfall,
        'slope_ari14d_interaction': slope * (rainfall * 8.0),
        'curvature_rainfall_interaction': curvature * rainfall
    }
    
    df = pd.DataFrame([features])
    
    # Validate features if expected list provided
    if expected_features:
        # Reorder columns to match training order
        df = df[expected_features]
        validate_features(df, expected_features)
    
    logger.info(
        "landslide_features_built",
        num_features=len(df.columns),
        lat=lat,
        lon=lon
    )
    
    return df
