"""
Test script for Weather ETL Pipeline (Task 7)

Tests:
1. Historical weather fetching (ERA5)
2. Forecast weather fetching (GFS)
3. Catchment sampling strategy
4. Zonal aggregation (Mean Areal Precipitation)
5. Time-series sanitization
6. Caching performance

Uses real Assam catchment from previous tasks.

Author: NEXUS-AI Team
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
import numpy as np

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.environmental.tasks.etl import (
    fetch_historical_weather,
    fetch_forecast_weather,
    aggregate_rainfall_to_catchment,
    sanitize_timeseries,
    _generate_sampling_points
)
from app.modules.geospatial.hydrology.catchment import catchment_to_polygon
from app.core.logging import configure_logger

# Configure logging
configure_logger()


def test_catchment_sampling():
    """Test 1: Catchment Sampling Strategy"""
    print("\n" + "="*60)
    print("TEST 1: Catchment Sampling Strategy")
    print("="*60)
    
    # Small catchment (< 100 km²)
    small_catchment = {
        "type": "Polygon",
        "coordinates": [[
            [91.5, 26.0],
            [91.55, 26.0],
            [91.55, 26.05],
            [91.5, 26.05],
            [91.5, 26.0]
        ]]
    }
    
    points = _generate_sampling_points(small_catchment)
    print(f"\n[Small Catchment] Sampling points: {len(points)}")
    assert len(points) == 1, "Small catchment should have 1 point"
    print(f"  Centroid: {points[0]}")
    print("[PASS] Small catchment sampling")
    
    # Medium catchment (100-1000 km²)
    # ~0.3° x 0.3° ≈ 900 km² at 26°N
    medium_catchment = {
        "type": "Polygon",
        "coordinates": [[
            [91.0, 26.0],
            [91.3, 26.0],
            [91.3, 26.3],
            [91.0, 26.3],
            [91.0, 26.0]
        ]]
    }
    
    points = _generate_sampling_points(medium_catchment)
    print(f"\n[Medium Catchment] Sampling points: {len(points)}")
    assert 1 <= len(points) <= 5, f"Medium catchment should have 1-5 points, got {len(points)}"
    print(f"  Points: {points[:3]}...")  # Show first 3
    print("[PASS] Medium catchment sampling")
    
    # Large catchment (> 1000 km²)
    # ~2° x 2° ≈ 40,000 km² at 26°N
    large_catchment = {
        "type": "Polygon",
        "coordinates": [[
            [90.0, 25.0],
            [92.0, 25.0],
            [92.0, 27.0],
            [90.0, 27.0],
            [90.0, 25.0]
        ]]
    }
    
    points = _generate_sampling_points(large_catchment)
    print(f"\n[Large Catchment] Sampling points: {len(points)}")
    assert 1 <= len(points) <= 10, f"Large catchment should have 1-10 points, got {len(points)}"
    print(f"  Points: {points[:3]}...")  # Show first 3
    print("[PASS] Large catchment sampling")


def test_historical_weather():
    """Test 2: Historical Weather Fetching"""
    print("\n" + "="*60)
    print("TEST 2: Historical Weather Fetching (ERA5)")
    print("="*60)
    
    # Use Assam catchment
    catchment = {
        "type": "Polygon",
        "coordinates": [[
            [91.5, 26.0],
            [91.7, 26.0],
            [91.7, 26.2],
            [91.5, 26.2],
            [91.5, 26.0]
        ]]
    }
    
    # Fetch 7 days of historical data
    start_date = date(2024, 6, 1)  # Monsoon season in Assam
    end_date = date(2024, 6, 7)
    
    print(f"\nFetching historical data: {start_date} to {end_date}")
    print("Variables: precipitation, temperature_2m")
    
    df = fetch_historical_weather(
        catchment,
        start_date,
        end_date,
        variables=['precipitation', 'temperature_2m']
    )
    
    print(f"\n[OK] Data fetched: {len(df)} rows")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Validation
    assert 'timestamp' in df.columns, "Missing timestamp column"
    assert 'precipitation' in df.columns, "Missing precipitation column"
    assert 'temperature_2m' in df.columns, "Missing temperature_2m column"
    assert len(df) > 0, "No data returned"
    
    # Check data types
    assert pd.api.types.is_datetime64_any_dtype(df['timestamp']), "Timestamp not datetime"
    assert pd.api.types.is_numeric_dtype(df['precipitation']), "Precipitation not numeric"
    
    # Check data range
    print(f"\nData Summary:")
    print(f"  Precipitation: min={df['precipitation'].min():.2f}, max={df['precipitation'].max():.2f}, mean={df['precipitation'].mean():.2f} mm")
    print(f"  Temperature: min={df['temperature_2m'].min():.2f}, max={df['temperature_2m'].max():.2f}, mean={df['temperature_2m'].mean():.2f} °C")
    
    print("\n[PASS] Historical weather fetching")
    
    return df


def test_forecast_weather():
    """Test 3: Forecast Weather Fetching"""
    print("\n" + "="*60)
    print("TEST 3: Forecast Weather Fetching (GFS)")
    print("="*60)
    
    # Use Assam catchment
    catchment = {
        "type": "Polygon",
        "coordinates": [[
            [91.5, 26.0],
            [91.7, 26.0],
            [91.7, 26.2],
            [91.5, 26.2],
            [91.5, 26.0]
        ]]
    }
    
    print(f"\nFetching 7-day forecast")
    print("Variables: precipitation")
    
    df = fetch_forecast_weather(
        catchment,
        horizon_days=7,
        variables=['precipitation']
    )
    
    print(f"\n[OK] Forecast fetched: {len(df)} rows")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Validation
    assert 'timestamp' in df.columns, "Missing timestamp column"
    assert 'precipitation' in df.columns, "Missing precipitation column"
    assert len(df) > 0, "No forecast data returned"
    
    # Check forecast is in the future
    first_timestamp = df['timestamp'].iloc[0]
    print(f"\nForecast starts: {first_timestamp}")
    
    # Ensure first_timestamp is timezone-aware for comparison if it's not
    if first_timestamp.tzinfo is None:
        first_timestamp = first_timestamp.tz_localize('UTC')
        
    # Allow up to 48 hours in the past to account for timezones and model run delays
    # (Forecasts usually start at 00:00 UTC of the current or previous day)
    threshold = pd.Timestamp.now(tz='UTC') - pd.Timedelta(hours=48)
    assert first_timestamp >= threshold, f"Forecast too old: {first_timestamp} < {threshold}"
    
    print(f"\nForecast Summary:")
    print(f"  Precipitation: min={df['precipitation'].min():.2f}, max={df['precipitation'].max():.2f}, mean={df['precipitation'].mean():.2f} mm")
    
    print("\n[PASS] Forecast weather fetching")
    
    return df


def test_catchment_aggregation(weather_df):
    """Test 4: Catchment Aggregation"""
    print("\n" + "="*60)
    print("TEST 4: Catchment Aggregation")
    print("="*60)
    
    catchment_id = "assam_test_001"
    
    print(f"\nAggregating weather data for catchment: {catchment_id}")
    
    df = aggregate_rainfall_to_catchment(weather_df, catchment_id)
    
    print(f"\n[OK] Aggregated: {len(df)} rows")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Validation
    assert 'timestamp' in df.columns, "Missing timestamp"
    assert 'catchment_id' in df.columns, "Missing catchment_id"
    assert 'rainfall_mm' in df.columns, "Missing rainfall_mm"
    assert (df['catchment_id'] == catchment_id).all(), "Catchment ID mismatch"
    
    print(f"\nAggregated Data:")
    print(f"  Catchment ID: {catchment_id}")
    print(f"  Total rainfall: {df['rainfall_mm'].sum():.2f} mm")
    print(f"  Mean hourly rainfall: {df['rainfall_mm'].mean():.2f} mm")
    
    print("\n[PASS] Catchment aggregation")
    
    return df


def test_timeseries_sanitization():
    """Test 5: Time-Series Sanitization"""
    print("\n" + "="*60)
    print("TEST 5: Time-Series Sanitization")
    print("="*60)
    
    # Create synthetic time series with gaps and duplicates
    timestamps = pd.date_range('2024-01-01', periods=100, freq='1h')
    
    # Remove some timestamps to create gaps
    gaps_to_remove = [10, 11, 12, 50, 51, 52, 53, 54, 55, 56, 57, 58]  # 3-hour and 9-hour gaps
    timestamps = timestamps.delete(gaps_to_remove)
    
    # Add duplicates
    timestamps = timestamps.append(pd.DatetimeIndex([timestamps[5], timestamps[20]]))
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'rainfall_mm': np.random.uniform(0, 10, len(timestamps)),
        'catchment_id': 'test_001'
    })
    
    print(f"\nOriginal data: {len(df)} rows")
    print(f"  Duplicates: 2")
    print(f"  Gaps: 3-hour gap, 9-hour gap")
    
    # Sanitize
    sanitized = sanitize_timeseries(df, max_gap_hours=6)
    
    print(f"\nSanitized data: {len(sanitized)} rows")
    
    # Check quality flags
    good_count = (sanitized['quality_flag'] == 'good').sum()
    interpolated_count = (sanitized['quality_flag'] == 'interpolated').sum()
    gap_count = (sanitized['quality_flag'] == 'gap').sum()
    
    print(f"\nQuality Flags:")
    print(f"  Good: {good_count}")
    print(f"  Interpolated: {interpolated_count}")
    print(f"  Gap (not filled): {gap_count}")
    
    # Validation
    assert sanitized['timestamp'].is_monotonic_increasing, "Timestamp not monotonic"
    assert not sanitized.duplicated(subset=['timestamp']).any(), "Duplicates still present"
    assert interpolated_count > 0, "No interpolation performed"
    assert gap_count > 0, "Long gap not flagged"
    
    print("\n[PASS] Time-series sanitization")


def test_caching():
    """Test 6: Caching Performance"""
    print("\n" + "="*60)
    print("TEST 6: Caching Performance")
    print("="*60)
    
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
    
    start_date = date(2024, 5, 1)
    end_date = date(2024, 5, 3)
    
    print(f"\nFirst fetch (should hit API):")
    import time
    start_time = time.time()
    
    df1 = fetch_historical_weather(catchment, start_date, end_date)
    
    first_duration = time.time() - start_time
    print(f"  Duration: {first_duration:.2f}s")
    print(f"  Rows: {len(df1)}")
    
    print(f"\nSecond fetch (should hit cache):")
    start_time = time.time()
    
    df2 = fetch_historical_weather(catchment, start_date, end_date)
    
    second_duration = time.time() - start_time
    print(f"  Duration: {second_duration:.2f}s")
    print(f"  Rows: {len(df2)}")
    
    # Validation
    assert len(df1) == len(df2), "Cache returned different data"
    assert second_duration < first_duration, "Cache not faster than API"
    
    speedup = first_duration / second_duration
    print(f"\nCache speedup: {speedup:.1f}x faster")
    
    print("\n[PASS] Caching performance")


def main():
    """Run all tests"""
    print("="*60)
    print("WEATHER ETL PIPELINE TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Sampling
        test_catchment_sampling()
        
        # Test 2: Historical weather
        historical_df = test_historical_weather()
        
        # Test 3: Forecast weather
        forecast_df = test_forecast_weather()
        
        # Test 4: Aggregation
        aggregated_df = test_catchment_aggregation(historical_df)
        
        # Test 5: Sanitization
        test_timeseries_sanitization()
        
        # Test 6: Caching
        test_caching()
        
        # Summary
        print("\n" + "="*60)
        print("[PASS] ALL TESTS PASSED")
        print("="*60)
        
        print("\nKey Validations:")
        print("  [OK] Catchment sampling strategy working")
        print("  [OK] Historical weather (ERA5) fetched successfully")
        print("  [OK] Forecast weather (GFS) fetched successfully")
        print("  [OK] Catchment aggregation produces ML-ready format")
        print("  [OK] Time-series sanitization handles gaps and duplicates")
        print("  [OK] Caching improves performance")
        
        print("\nML-Ready Output Schema:")
        print(aggregated_df.head())
        
        print("\nDual-Hazard Compatibility:")
        print("  -> Flood forecasting: Use 24h, 72h cumulative rainfall")
        print("  -> Landslide triggering: Use antecedent rainfall (7d, 30d)")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
