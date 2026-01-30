"""
Time-Series Cleaning Utilities for Hydrological Data

Provides robust cleaning and validation functions for water level time series
and other environmental signals. Designed for ML label generation where data
quality is critical.

Key Features:
- Physical validation (remove impossible jumps)
- Gap handling (interpolate short, flag long)
- Outlier detection (IQR-based)
- Auditability (quality flags on all modifications)

Author: NEXUS-AI Team
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("signal_cleaning")


def validate_gauge_data(df: pd.DataFrame) -> Tuple[bool, list]:
    """
    Validate gauge data for required columns and basic sanity checks.
    
    Args:
        df: DataFrame with gauge data
    
    Returns:
        (is_valid, error_messages)
    
    Example:
        >>> is_valid, errors = validate_gauge_data(df)
        >>> if not is_valid:
        ...     print(f"Validation failed: {errors}")
    """
    errors = []
    
    # Check required columns
    required_cols = ['timestamp', 'water_level']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors
    
    # Check for empty dataframe
    if len(df) == 0:
        errors.append("DataFrame is empty")
        return False, errors
    
    # Check timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        errors.append("'timestamp' column must be datetime type")
    
    # Check for negative water levels
    if (df['water_level'] < 0).any():
        neg_count = (df['water_level'] < 0).sum()
        errors.append(f"Found {neg_count} negative water level values")
    
    # Check for monotonic timestamps
    if not df['timestamp'].is_monotonic_increasing:
        errors.append("Timestamps are not monotonically increasing")
    
    # Check for duplicate timestamps
    if df['timestamp'].duplicated().any():
        dup_count = df['timestamp'].duplicated().sum()
        errors.append(f"Found {dup_count} duplicate timestamps")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def detect_anomalies(
    df: pd.DataFrame,
    column: str,
    method: str = 'iqr',
    threshold: float = 3.0
) -> pd.Series:
    """
    Detect anomalies in a time series using statistical methods.
    
    Args:
        df: DataFrame containing the data
        column: Column name to check for anomalies
        method: Detection method ('iqr' or 'zscore')
        threshold: Threshold for anomaly detection
            - For 'iqr': multiplier for IQR (default 3.0)
            - For 'zscore': number of standard deviations (default 3.0)
    
    Returns:
        Boolean Series where True indicates an anomaly
    
    Example:
        >>> anomalies = detect_anomalies(df, 'water_level', method='iqr')
        >>> print(f"Found {anomalies.sum()} anomalies")
    """
    values = df[column].dropna()
    
    if method == 'iqr':
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        anomalies = (df[column] < lower_bound) | (df[column] > upper_bound)
        
        logger.info(
            "iqr_anomaly_detection",
            column=column,
            Q1=round(Q1, 2),
            Q3=round(Q3, 2),
            IQR=round(IQR, 2),
            lower_bound=round(lower_bound, 2),
            upper_bound=round(upper_bound, 2),
            anomalies_found=anomalies.sum()
        )
    
    elif method == 'zscore':
        mean = values.mean()
        std = values.std()
        
        z_scores = np.abs((df[column] - mean) / std)
        anomalies = z_scores > threshold
        
        logger.info(
            "zscore_anomaly_detection",
            column=column,
            mean=round(mean, 2),
            std=round(std, 2),
            threshold=threshold,
            anomalies_found=anomalies.sum()
        )
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'iqr' or 'zscore'")
    
    return anomalies


def clean_water_level_timeseries(
    df: pd.DataFrame,
    max_jump_mh: Optional[float] = None,
    max_gap_hours: Optional[int] = None
) -> pd.DataFrame:
    """
    Clean water level time series with physical validation and gap handling.
    
    This is the CRITICAL function for ML label generation. Bad labels = bad ML.
    
    Cleaning steps:
    1. Remove duplicate timestamps
    2. Sort by timestamp
    3. Detect and remove physically impossible jumps
    4. Interpolate short gaps (≤ max_gap_hours)
    5. Flag long gaps (> max_gap_hours) without filling
    
    Args:
        df: DataFrame with columns ['timestamp', 'water_level', ...]
        max_jump_mh: Maximum allowed jump in meters/hour (default from config)
        max_gap_hours: Maximum gap to interpolate in hours (default from config)
    
    Returns:
        Cleaned DataFrame with added 'quality_flag' column
        
    Quality flags:
        - 'good': Original, unmodified data
        - 'interpolated': Filled via linear interpolation
        - 'gap': Long gap detected (not filled)
        - 'jump_removed': Physically impossible jump removed
    
    Example:
        >>> cleaned = clean_water_level_timeseries(df)
        >>> good_data = cleaned[cleaned['quality_flag'] == 'good']
    """
    if max_jump_mh is None:
        max_jump_mh = settings.MAX_WATER_LEVEL_JUMP_MH
    
    if max_gap_hours is None:
        max_gap_hours = settings.MAX_GAP_HOURS_INTERPOLATE
    
    logger.info(
        "cleaning_water_level_timeseries",
        rows=len(df),
        max_jump_mh=max_jump_mh,
        max_gap_hours=max_gap_hours
    )
    
    # Validate input
    is_valid, errors = validate_gauge_data(df)
    if not is_valid:
        logger.error("validation_failed", errors=errors)
        # Return empty DataFrame with proper schema
        return pd.DataFrame(columns=list(df.columns) + ['quality_flag'])
    
    df = df.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Remove duplicates
    duplicates = df.duplicated(subset=['timestamp'], keep='first')
    if duplicates.any():
        num_duplicates = duplicates.sum()
        logger.warning("duplicates_removed", count=num_duplicates)
        df = df[~duplicates].reset_index(drop=True)
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Add quality flag
    df['quality_flag'] = 'good'
    
    # Calculate time differences and water level changes
    df['time_diff_hours'] = df['timestamp'].diff().dt.total_seconds() / 3600
    df['level_diff'] = df['water_level'].diff()
    
    # Detect physically impossible jumps
    # Jump rate = meters / hour
    df['jump_rate'] = df['level_diff'].abs() / df['time_diff_hours']
    
    impossible_jumps = df['jump_rate'] > max_jump_mh
    if impossible_jumps.any():
        num_jumps = impossible_jumps.sum()
        logger.warning(
            "impossible_jumps_detected",
            count=num_jumps,
            max_jump_mh=max_jump_mh
        )
        
        # Mark these rows for removal
        df.loc[impossible_jumps, 'quality_flag'] = 'jump_removed'
        
        # Remove the impossible jump rows
        df = df[df['quality_flag'] != 'jump_removed'].reset_index(drop=True)
        
        # Recalculate diffs after removal
        df['time_diff_hours'] = df['timestamp'].diff().dt.total_seconds() / 3600
        df['level_diff'] = df['water_level'].diff()
    
    # Detect gaps
    expected_interval_hours = df['time_diff_hours'].median()
    gap_threshold = expected_interval_hours * 1.5  # Allow 50% tolerance
    
    gaps = df['time_diff_hours'] > gap_threshold
    
    if gaps.any():
        num_gaps = gaps.sum()
        logger.info("gaps_detected", count=num_gaps)
        
        interpolated_rows = []
        
        # Process each gap
        for idx in df[gaps].index:
            gap_hours = df.loc[idx, 'time_diff_hours']
            
            if gap_hours <= max_gap_hours:
                # Interpolate short gaps
                prev_idx = idx - 1
                
                start_time = df.loc[prev_idx, 'timestamp']
                end_time = df.loc[idx, 'timestamp']
                start_level = df.loc[prev_idx, 'water_level']
                end_level = df.loc[idx, 'water_level']
                
                # Create missing timestamps
                num_missing = int(gap_hours / expected_interval_hours) - 1
                
                if num_missing > 0:
                    logger.info("gap_interpolated", gap_hours=gap_hours, num_points=num_missing)
                    
                    for i in range(1, num_missing + 1):
                        # Linear interpolation
                        weight = i / (num_missing + 1)
                        interp_time = start_time + (end_time - start_time) * weight
                        interp_level = start_level + (end_level - start_level) * weight
                        
                        row = {
                            'timestamp': interp_time,
                            'water_level': interp_level,
                            'quality_flag': 'interpolated'
                        }
                        
                        # Copy other columns from previous row
                        for col in df.columns:
                            if col not in ['timestamp', 'water_level', 'quality_flag', 
                                          'time_diff_hours', 'level_diff', 'jump_rate']:
                                row[col] = df.loc[prev_idx, col]
                        
                        interpolated_rows.append(row)
            else:
                # Long gap - flag but don't interpolate
                df.at[idx, 'quality_flag'] = 'gap'
                logger.warning("long_gap_detected", gap_hours=gap_hours)
        
        # Add interpolated rows
        if interpolated_rows:
            df = pd.concat([df, pd.DataFrame(interpolated_rows)], ignore_index=True)
            df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Drop temporary columns
    df = df.drop(columns=['time_diff_hours', 'level_diff', 'jump_rate'], errors='ignore')
    
    # Final validation
    assert df['timestamp'].is_monotonic_increasing, "Timestamps not monotonic after cleaning"
    
    logger.info(
        "cleaning_complete",
        final_rows=len(df),
        good=int((df['quality_flag'] == 'good').sum()),
        interpolated=int((df['quality_flag'] == 'interpolated').sum()),
        gaps=int((df['quality_flag'] == 'gap').sum())
    )
    
    return df
