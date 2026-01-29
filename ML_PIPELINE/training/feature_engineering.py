"""
Feature Engineering for Flood Prediction

Creates lag features and rolling aggregations from time series data.
Prevents data leakage by only using historical information.

Author: NEXUS-AI Team
"""

from typing import List, Optional
import pandas as pd
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("feature_engineering")


def create_lag_features(
    df: pd.DataFrame,
    columns: List[str],
    lags: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Create lagged versions of specified columns.
    
    Args:
        df: DataFrame with time series data (must be sorted by timestamp)
        columns: List of column names to create lags for
        lags: List of lag periods in days (default from config)
    
    Returns:
        DataFrame with additional lag columns
    
    Example:
        >>> df_lagged = create_lag_features(df, ['rainfall_mm'], lags=[1, 2, 3])
        >>> # Creates: rainfall_mm_lag_1, rainfall_mm_lag_2, rainfall_mm_lag_3
    """
    if lags is None:
        lags = settings.LAG_DAYS
    
    df = df.copy()
    
    # Group by station_id if present
    group_col = 'station_id' if 'station_id' in df.columns else None
    
    # Determine the frequency of the data
    if 'timestamp' in df.columns and len(df) > 1:
        time_diff = pd.to_datetime(df['timestamp']).diff().dropna()
        freq_hours = time_diff.median().total_seconds() / 3600
    else:
        freq_hours = 1  # Default to hourly
    
    for col in columns:
        if col not in df.columns:
            logger.warning("column_not_found", column=col)
            continue
        
        for lag in lags:
            lag_col_name = f"{col}_lag_{lag}"
            
            # Calculate shift periods based on data frequency
            # lag is in days, so shift = lag_days * (24 hours/day) / hours_per_period
            shift_periods = int(lag * 24 / freq_hours)
            
            if group_col:
                # Lag within each station
                df[lag_col_name] = df.groupby(group_col)[col].shift(shift_periods)
            else:
                df[lag_col_name] = df[col].shift(shift_periods)
    
    num_lag_features = len(columns) * len(lags)
    logger.info(
        "lag_features_created",
        columns=columns,
        lags=lags,
        num_features=num_lag_features
    )
    
    return df


def create_rolling_features(
    df: pd.DataFrame,
    columns: List[str],
    windows: Optional[List[int]] = None,
    aggregations: List[str] = ['sum']
) -> pd.DataFrame:
    """
    Create rolling window aggregations.
    
    Args:
        df: DataFrame with time series data (must be sorted by timestamp)
        columns: List of column names to aggregate
        windows: List of window sizes in days (default from config)
        aggregations: List of aggregation functions ('sum', 'mean', 'max')
    
    Returns:
        DataFrame with additional rolling features
    
    Example:
        >>> df_rolled = create_rolling_features(
        ...     df,
        ...     ['rainfall_mm'],
        ...     windows=[3, 5, 7],
        ...     aggregations=['sum']
        ... )
        >>> # Creates: rainfall_mm_3d_sum, rainfall_mm_5d_sum, rainfall_mm_7d_sum
    """
    if windows is None:
        windows = settings.ROLLING_WINDOWS
    
    df = df.copy()
    
    # Group by station_id if present
    group_col = 'station_id' if 'station_id' in df.columns else None
    
    # Determine the frequency of the data
    if 'timestamp' in df.columns and len(df) > 1:
        time_diff = pd.to_datetime(df['timestamp']).diff().dropna()
        freq_hours = time_diff.median().total_seconds() / 3600
    else:
        freq_hours = 1  # Default to hourly
    
    for col in columns:
        if col not in df.columns:
            logger.warning("column_not_found", column=col)
            continue
        
        for window in windows:
            for agg in aggregations:
                feature_name = f"{col}_{window}d_{agg}"
                
                # Calculate rolling window in periods based on data frequency
                # window is in days, so periods = window_days * (24 hours/day) / hours_per_period
                window_periods = int(window * 24 / freq_hours)
                
                if group_col:
                    # Rolling within each station
                    df[feature_name] = df.groupby(group_col)[col].transform(
                        lambda x: x.rolling(window=window_periods, min_periods=1).agg(agg)
                    )
                else:
                    df[feature_name] = df[col].rolling(window=window_periods, min_periods=1).agg(agg)
    
    num_rolling_features = len(columns) * len(windows) * len(aggregations)
    logger.info(
        "rolling_features_created",
        columns=columns,
        windows=windows,
        aggregations=aggregations,
        num_features=num_rolling_features
    )
    
    return df


def add_static_features(
    df: pd.DataFrame,
    terrain_features: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Ensure static terrain features are present.
    
    Args:
        df: DataFrame (terrain features should already be in dataset)
        terrain_features: List of terrain feature names to verify
   
    Returns:
        DataFrame (unchanged if features present)
    
    Note:
        Static features are already added in dataset_builder.
        This function just verifies they exist.
    """
    if terrain_features is None:
        terrain_features = ['catchment_area', 'mean_hand', 'mean_slope']
    
    present_features = [f for f in terrain_features if f in df.columns]
    missing_features = [f for f in terrain_features if f not in df.columns]
    
    if missing_features:
        logger.warning("missing_terrain_features", missing=missing_features)
    
    logger.info("static_features_verified", features=present_features)
    
    return df


def engineer_flood_features(
    df: pd.DataFrame,
    rainfall_column: str = 'rainfall_mm',
    temperature_column: Optional[str] = 'temperature_2m'
) -> pd.DataFrame:
    """
    Main feature engineering pipeline for flood prediction.
    
    Creates:
    - Lag features: t-1, t-2, t-3, t-5, t-7 days
    - Rolling sums: 3d, 5d, 7d
    - Static terrain features (already in dataset)
    
    Args:
        df: Raw dataset from dataset_builder
        rainfall_column: Name of rainfall column
        temperature_column: Name of temperature column (optional)
    
    Returns:
        DataFrame with engineered features
    
    Example:
        >>> df = build_flood_dataset(...)
        >>> df_features = engineer_flood_features(df)
        >>> print(df_features.columns)
    """
    logger.info("starting_feature_engineering", rows=len(df))
    
    df = df.copy()
    
    # Ensure sorted by station and time
    if 'station_id' in df.columns:
        df = df.sort_values(['station_id', 'timestamp']).reset_index(drop=True)
    else:
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 1. Create lag features for rainfall
    columns_to_lag = [rainfall_column]
    if temperature_column and temperature_column in df.columns:
        columns_to_lag.append(temperature_column)
    
    df = create_lag_features(df, columns_to_lag)
    
    # 2. Create rolling sum features for rainfall
    df = create_rolling_features(
        df,
        [rainfall_column],
        aggregations=['sum']
    )
    
    # 3. Verify static terrain features
    df = add_static_features(df)
    
    # 4. Drop rows with NaN in lag features (early timesteps)
    # This prevents data leakage - we can't use data we wouldn't have historically
    # Only check lag features, not all columns (some columns like event_id may have NaN)
    before_drop = len(df)
    
    # Identify lag feature columns
    lag_cols = [col for col in df.columns if '_lag_' in col]
    
    if lag_cols:
        # Drop only rows where lag features are NaN
        df = df.dropna(subset=lag_cols).reset_index(drop=True)
    
    after_drop = len(df)
    
    if before_drop > after_drop:
        logger.info(
            "dropped_incomplete_rows",
            dropped=before_drop - after_drop,
            reason="NaN in lag features (expected for early timestamps)"
        )
    
    # 5. Identify feature columns (exclude metadata and target)
    exclude_cols = {
        'timestamp', 'station_id', 'water_level', 'warning_level', 'danger_level',
        'label', 'quality_flag', 'river', 'location', 'lead_time_hours',
        'event_id', 'event_duration_hours', 'peak_level'
    }
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    logger.info(
        "feature_engineering_complete",
        final_rows=len(df),
        num_features=len(feature_cols),
        features=feature_cols
    )
    
    return df


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of feature column names (excluding metadata and target).
    
    Args:
        df: DataFrame with engineered features
    
    Returns:
        List of feature column names
    """
    exclude_cols = {
        'timestamp', 'station_id', 'water_level', 'warning_level', 'danger_level',
        'label', 'quality_flag', 'river', 'location', 'lead_time_hours',
        'event_id', 'event_duration_hours', 'peak_level'
    }
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    return feature_cols


def create_antecedent_rainfall_index(
    df: pd.DataFrame,
    rainfall_column: str = 'rainfall_mm',
    windows: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Create Antecedent Rainfall Index (ARI) features for landslide prediction.
    
    ARI represents cumulative soil moisture from past rainfall.
    Uses simple cumulative sums over different windows.
    
    Args:
        df: DataFrame with rainfall data (sorted by time)
        rainfall_column: Name of rainfall column
        windows: List of window sizes in days (default: [3, 7, 14, 30])
    
    Returns:
        DataFrame with ARI features added
    
    Example:
        >>> df = create_antecedent_rainfall_index(df, windows=[7, 14, 30])
        >>> # Creates: rainfall_ari_7d, rainfall_ari_14d, rainfall_ari_30d
    """
    if windows is None:
        windows = [3, 7, 14, 30]
    
    df = df.copy()
    
    # Group by grid_id if present
    group_col = 'grid_id' if 'grid_id' in df.columns else None
    
    # Determine frequency
    if 'date' in df.columns and len(df) > 1:
        time_diff = pd.to_datetime(df['date']).diff().dropna()
        freq_hours = time_diff.median().total_seconds() / 3600
    else:
        freq_hours = 24  # Daily data
    
    for window in windows:
        feature_name = f"{rainfall_column}_ari_{window}d"
        
        # Calculate rolling sum
        window_periods = int(window * 24 / freq_hours)
        
        if group_col:
            df[feature_name] = df.groupby(group_col)[rainfall_column].transform(
                lambda x: x.rolling(window=window_periods, min_periods=1).sum()
            )
        else:
            df[feature_name] = df[rainfall_column].rolling(window=window_periods, min_periods=1).sum()
    
    logger.info(
        "ari_features_created",
        windows=windows,
        num_features=len(windows)
    )
    
    return df


def create_physics_interactions(
    df: pd.DataFrame,
    rainfall_column: str = 'rainfall_mm'
) -> pd.DataFrame:
    """
    Create physics-informed interaction features for landslide prediction.
    
    Interactions:
    - slope × rainfall: Steep slopes + heavy rain → high risk
    - curvature × rainfall: Concave slopes accumulate water
    
    Args:
        df: DataFrame with slope, curvature, rainfall
        rainfall_column: Name of rainfall column
    
    Returns:
        DataFrame with interaction features
    """
    df = df.copy()
    
    interactions_created = []
    
    # Slope × Rainfall interaction
    if 'slope' in df.columns and rainfall_column in df.columns:
        df['slope_rainfall_interaction'] = df['slope'] * df[rainfall_column]
        interactions_created.append('slope_rainfall_interaction')
    
    # Slope × ARI (if ARI exists)
    ari_cols = [col for col in df.columns if 'ari_14d' in col]
    if 'slope' in df.columns and ari_cols:
        df['slope_ari14d_interaction'] = df['slope'] * df[ari_cols[0]]
        interactions_created.append('slope_ari14d_interaction')
    
    # Curvature × Rainfall interaction
    if 'curvature' in df.columns and rainfall_column in df.columns:
        df['curvature_rainfall_interaction'] = df['curvature'] * df[rainfall_column]
        interactions_created.append('curvature_rainfall_interaction')
    
    logger.info(
        "physics_interactions_created",
        features=interactions_created
    )
    
    return df


def engineer_landslide_features(
    df: pd.DataFrame,
    rainfall_column: str = 'rainfall_mm'
) -> pd.DataFrame:
    """
    Main feature engineering pipeline for landslide prediction.
    
    Creates:
    - Antecedent Rainfall Index (ARI): 3d, 7d, 14d, 30d
    - Lag features: t-1, t-3, t-7 days
    - Rolling sums: 3d, 7d
    - Physics interactions: slope×rainfall, curvature×rainfall
    - Static terrain features (slope, aspect, curvature)
    
    Args:
        df: Raw dataset from dataset_builder_landslide
        rainfall_column: Name of rainfall column
    
    Returns:
        DataFrame with engineered features
    
    Example:
        >>> df = build_landslide_dataset(...)
        >>> df_features = engineer_landslide_features(df)
    """
    logger.info("starting_landslide_feature_engineering", rows=len(df))
    
    df = df.copy()
    
    # Ensure sorted by grid and time
    if 'grid_id' in df.columns:
        df = df.sort_values(['grid_id', 'date']).reset_index(drop=True)
    else:
        df = df.sort_values('date').reset_index(drop=True)
    
    # 1. Create Antecedent Rainfall Index (ARI)
    df = create_antecedent_rainfall_index(df, rainfall_column, windows=[3, 7, 14, 30])
    
    # 2. Create lag features (shorter lags for landslides)
    columns_to_lag = [rainfall_column]
    if 'temperature' in df.columns:
        columns_to_lag.append('temperature')
    
    df = create_lag_features(df, columns_to_lag, lags=[1, 3, 7])
    
    # 3. Create rolling sums (redundant with ARI but kept for consistency)
    df = create_rolling_features(
        df,
        [rainfall_column],
        windows=[3, 7],
        aggregations=['sum']
    )
    
    # 4. Create physics-informed interactions
    df = create_physics_interactions(df, rainfall_column)
    
    # 5. Verify static terrain features
    df = add_static_features(df, terrain_features=['slope', 'aspect', 'curvature', 'elevation'])
    
    # 6. Drop rows with NaN in lag features
    before_drop = len(df)
    lag_cols = [col for col in df.columns if '_lag_' in col or '_ari_' in col]
    
    if lag_cols:
        df = df.dropna(subset=lag_cols).reset_index(drop=True)
    
    after_drop = len(df)
    
    if before_drop > after_drop:
        logger.info(
            "dropped_incomplete_rows",
            dropped=before_drop - after_drop,
            reason="NaN in lag/ARI features (expected for early timestamps)"
        )
    
    # 7. Identify feature columns
    exclude_cols = {
        'date', 'grid_id', 'label', 'num_events',
        'center_lon', 'center_lat', 'geometry'
    }
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    logger.info(
        "landslide_feature_engineering_complete",
        final_rows=len(df),
        num_features=len(feature_cols),
        features=feature_cols
    )
    
    return df
