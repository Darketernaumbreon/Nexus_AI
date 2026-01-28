"""
Test Script for Ground Truth Ingestion & Label Generation (Task 8)

Tests:
1. Time-series cleaning (physical validation, gap handling)
2. CWC flood gauge scraping
3. Flood label generation (binary labels, lead time, event grouping)
4. Landslide inventory ingestion (NASA GLC, custom CSV)

Author: NEXUS-AI Team
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.environmental.tasks.signal_cleaning import (
    validate_gauge_data,
    detect_anomalies,
    clean_water_level_timeseries
)
from app.modules.environmental.tasks.cwc_scraper import (
    fetch_cwc_station_data,
    generate_flood_labels,
    fetch_and_label_cwc_data
)
from app.modules.environmental.tasks.landslide_ingestion import (
    ingest_custom_csv,
    normalize_landslide_data,
    _parse_date_robust,
    _validate_coordinates
)
from app.core.logging import configure_logger

# Configure logging
configure_logger()


def test_gauge_validation():
    """Test 1: Gauge Data Validation"""
    print("\n" + "="*60)
    print("TEST 1: Gauge Data Validation")
    print("="*60)
    
    # Valid data
    valid_df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=10, freq='1h'),
        'water_level': np.linspace(45, 50, 10)
    })
    
    is_valid, errors = validate_gauge_data(valid_df)
    print(f"\n[Valid Data] is_valid={is_valid}, errors={errors}")
    assert is_valid, "Valid data should pass validation"
    print("[PASS] Valid data validation")
    
    # Invalid data - negative water levels
    invalid_df = valid_df.copy()
    invalid_df.loc[5, 'water_level'] = -10.0
    
    is_valid, errors = validate_gauge_data(invalid_df)
    print(f"\n[Negative Levels] is_valid={is_valid}, errors={errors}")
    assert not is_valid, "Negative water levels should fail validation"
    assert any('negative' in str(e).lower() for e in errors)
    print("[PASS] Negative water level detection")
    
    # Invalid data - duplicate timestamps
    dup_df = pd.concat([valid_df, valid_df.iloc[[0]]], ignore_index=True)
    
    is_valid, errors = validate_gauge_data(dup_df)
    print(f"\n[Duplicates] is_valid={is_valid}, errors={errors}")
    assert not is_valid, "Duplicate timestamps should fail validation"
    print("[PASS] Duplicate timestamp detection")


def test_anomaly_detection():
    """Test 2: Anomaly Detection"""
    print("\n" + "="*60)
    print("TEST 2: Anomaly Detection")
    print("="*60)
    
    # Create data with outliers
    np.random.seed(42)
    normal_data = np.random.normal(50, 2, 100)
    outliers = [70, 75, 20, 15]  # Clear outliers
    
    data = np.concatenate([normal_data, outliers])
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=len(data), freq='1h'),
        'water_level': data
    })
    
    # IQR method
    anomalies_iqr = detect_anomalies(df, 'water_level', method='iqr', threshold=3.0)
    print(f"\n[IQR Method] Anomalies detected: {anomalies_iqr.sum()}")
    assert anomalies_iqr.sum() >= 4, "Should detect at least 4 outliers"
    print("[PASS] IQR anomaly detection")
    
    # Z-score method
    anomalies_z = detect_anomalies(df, 'water_level', method='zscore', threshold=3.0)
    print(f"[Z-Score Method] Anomalies detected: {anomalies_z.sum()}")
    assert anomalies_z.sum() >= 4, "Should detect at least 4 outliers"
    print("[PASS] Z-score anomaly detection")


def test_timeseries_cleaning():
    """Test 3: Time-Series Cleaning"""
    print("\n" + "="*60)
    print("TEST 3: Time-Series Cleaning")
    print("="*60)
    
    # Create synthetic data with known issues
    timestamps = pd.date_range('2024-01-01', periods=100, freq='1h')
    water_levels = np.linspace(45, 50, 100) + np.random.normal(0, 0.1, 100)
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'water_level': water_levels,
        'warning_level': 49.0,
        'danger_level': 50.0,
        'station_id': 'TEST001'
    })
    
    # Add a physically impossible jump (10m in 1 hour)
    df.loc[50, 'water_level'] = 60.0
    
    # Remove some timestamps to create gaps
    gaps_to_remove = [20, 21, 22, 70, 71, 72, 73, 74, 75, 76, 77, 78]  # 3h and 9h gaps
    df = df.drop(gaps_to_remove).reset_index(drop=True)
    
    print(f"\nOriginal data: {len(df)} rows")
    print(f"  - Contains 1 impossible jump (10m/h)")
    print(f"  - Contains 2 gaps (3h, 9h)")
    
    # Note: We don't add duplicates here because the cleaning function
    # validates and rejects data with duplicates. The cleaning function
    # itself handles duplicate removal, so we test that separately.
    
    # Clean
    cleaned = clean_water_level_timeseries(df, max_jump_mh=3.0, max_gap_hours=6)
    
    print(f"\nCleaned data: {len(cleaned)} rows")
    
    # Check quality flags
    good_count = (cleaned['quality_flag'] == 'good').sum()
    interpolated_count = (cleaned['quality_flag'] == 'interpolated').sum()
    gap_count = (cleaned['quality_flag'] == 'gap').sum()
    
    print(f"\nQuality Flags:")
    print(f"  Good: {good_count}")
    print(f"  Interpolated: {interpolated_count}")
    print(f"  Gap (not filled): {gap_count}")
    
    # Validations
    assert cleaned['timestamp'].is_monotonic_increasing, "Timestamps not monotonic"
    assert not cleaned['timestamp'].duplicated().any(), "Duplicates still present"
    assert interpolated_count > 0, "No interpolation performed"
    assert gap_count > 0, "Long gap not flagged"
    assert (cleaned['water_level'] < 60).all(), "Impossible jump not removed"
    
    print("\n[PASS] Time-series cleaning")


def test_cwc_scraping():
    """Test 4: CWC Flood Gauge Scraping"""
    print("\n" + "="*60)
    print("TEST 4: CWC Flood Gauge Scraping")
    print("="*60)
    
    # Fetch mock data
    start_date = datetime(2024, 6, 1)
    end_date = datetime(2024, 6, 7)
    
    print(f"\nFetching CWC data: {start_date} to {end_date}")
    
    df = fetch_cwc_station_data("GUW001", start_date, end_date)
    
    print(f"\n[OK] Data fetched: {len(df)} rows")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Validation
    assert 'timestamp' in df.columns, "Missing timestamp column"
    assert 'water_level' in df.columns, "Missing water_level column"
    assert 'warning_level' in df.columns, "Missing warning_level column"
    assert 'danger_level' in df.columns, "Missing danger_level column"
    assert 'station_id' in df.columns, "Missing station_id column"
    assert len(df) > 0, "No data returned"
    
    print(f"\nData Summary:")
    print(f"  Water Level: min={df['water_level'].min():.2f}, max={df['water_level'].max():.2f}, mean={df['water_level'].mean():.2f} m")
    print(f"  Warning Level: {df['warning_level'].iloc[0]:.2f} m")
    print(f"  Danger Level: {df['danger_level'].iloc[0]:.2f} m")
    
    print("\n[PASS] CWC flood gauge scraping")
    
    return df


def test_flood_label_generation(gauge_df):
    """Test 5: Flood Label Generation"""
    print("\n" + "="*60)
    print("TEST 5: Flood Label Generation")
    print("="*60)
    
    print(f"\nGenerating flood labels...")
    
    labeled = generate_flood_labels(gauge_df)
    
    print(f"\n[OK] Labels generated: {len(labeled)} rows")
    print(f"\nFirst 5 rows:")
    print(labeled[['timestamp', 'water_level', 'danger_level', 'label', 'lead_time_hours', 'event_id']].head())
    
    # Validation
    assert 'label' in labeled.columns, "Missing label column"
    assert 'lead_time_hours' in labeled.columns, "Missing lead_time_hours column"
    assert 'event_id' in labeled.columns, "Missing event_id column"
    
    # Check label logic
    flood_mask = labeled['water_level'] >= labeled['danger_level']
    assert (labeled.loc[flood_mask, 'label'] == 1).all(), "Label should be 1 when water_level >= danger_level"
    assert (labeled.loc[~flood_mask, 'label'] == 0).all(), "Label should be 0 when water_level < danger_level"
    
    # Statistics
    num_flood_points = (labeled['label'] == 1).sum()
    num_events = labeled['event_id'].nunique()
    
    print(f"\nLabel Statistics:")
    print(f"  Total points: {len(labeled)}")
    print(f"  Flood points (label=1): {num_flood_points} ({100*num_flood_points/len(labeled):.1f}%)")
    print(f"  Flood events: {int(num_events)}")
    
    if num_events > 0:
        print(f"\nEvent Details:")
        for event_id in labeled['event_id'].dropna().unique():
            event_data = labeled[labeled['event_id'] == event_id]
            duration = event_data['event_duration_hours'].iloc[0]
            peak = event_data['peak_level'].iloc[0]
            print(f"  Event {int(event_id)}: Duration={duration:.1f}h, Peak={peak:.2f}m")
    
    print("\n[PASS] Flood label generation")


def test_landslide_ingestion():
    """Test 6: Landslide Inventory Ingestion"""
    print("\n" + "="*60)
    print("TEST 6: Landslide Inventory Ingestion")
    print("="*60)
    
    # Create mock landslide CSV
    mock_data = pd.DataFrame({
        'Date': ['2024-07-15', '2024-07-20', '2024-08-01'],
        'Latitude': [26.1234, 26.5678, 27.1234],
        'Longitude': [91.5678, 92.1234, 91.8765],
        'Type': ['landslide', 'debris_flow', 'landslide'],
        'Location': ['Assam District A', 'Assam District B', 'Assam District C']
    })
    
    # Save to temp file
    temp_csv = Path("temp_landslides.csv")
    mock_data.to_csv(temp_csv, index=False)
    
    print(f"\nCreated mock CSV: {temp_csv}")
    print(f"  Rows: {len(mock_data)}")
    
    # Define schema mapping
    schema_mapping = {
        'Date': 'timestamp',
        'Latitude': 'lat',
        'Longitude': 'lon',
        'Type': 'event_type',
        'Location': 'location_name'
    }
    
    # Ingest
    df = ingest_custom_csv(str(temp_csv), schema_mapping)
    
    print(f"\n[OK] Data ingested: {len(df)} rows")
    print(f"\nFirst 3 rows:")
    print(df.head())
    
    # Validation
    assert 'timestamp' in df.columns, "Missing timestamp column"
    assert 'lat' in df.columns, "Missing lat column"
    assert 'lon' in df.columns, "Missing lon column"
    assert 'event_type' in df.columns, "Missing event_type column"
    assert 'source' in df.columns, "Missing source column"
    assert len(df) == 3, "Should have 3 rows"
    
    # Normalize
    normalized = normalize_landslide_data(df)
    
    print(f"\n[OK] Data normalized: {len(normalized)} rows")
    
    # Cleanup
    temp_csv.unlink()
    
    print("\n[PASS] Landslide inventory ingestion")


def test_date_parsing():
    """Test 7: Robust Date Parsing"""
    print("\n" + "="*60)
    print("TEST 7: Robust Date Parsing")
    print("="*60)
    
    test_dates = [
        ('2024-01-15', datetime(2024, 1, 15)),
        ('2024/01/15', datetime(2024, 1, 15)),
        ('15-01-2024', datetime(2024, 1, 15)),
        ('15/01/2024', datetime(2024, 1, 15)),
        ('01/15/2024', datetime(2024, 1, 15)),
    ]
    
    print("\nTesting date formats:")
    for date_str, expected in test_dates:
        parsed = _parse_date_robust(date_str)
        print(f"  '{date_str}' -> {parsed}")
        assert parsed is not None, f"Failed to parse: {date_str}"
        assert parsed.date() == expected.date(), f"Incorrect parse: {date_str}"
    
    print("\n[PASS] Robust date parsing")


def test_coordinate_validation():
    """Test 8: Coordinate Validation"""
    print("\n" + "="*60)
    print("TEST 8: Coordinate Validation")
    print("="*60)
    
    # Valid India coordinates
    valid_coords = [
        (26.1445, 91.7362),  # Guwahati
        (28.6139, 77.2090),  # Delhi
        (19.0760, 72.8777),  # Mumbai
    ]
    
    print("\nTesting valid coordinates:")
    for lat, lon in valid_coords:
        is_valid = _validate_coordinates(lat, lon)
        print(f"  ({lat}, {lon}) -> {is_valid}")
        assert is_valid, f"Valid coordinate rejected: ({lat}, {lon})"
    
    # Invalid coordinates
    invalid_coords = [
        (51.5074, -0.1278),  # London (outside India)
        (40.7128, -74.0060),  # New York (outside India)
    ]
    
    print("\nTesting invalid coordinates:")
    for lat, lon in invalid_coords:
        is_valid = _validate_coordinates(lat, lon)
        print(f"  ({lat}, {lon}) -> {is_valid}")
        assert not is_valid, f"Invalid coordinate accepted: ({lat}, {lon})"
    
    print("\n[PASS] Coordinate validation")


def test_complete_pipeline():
    """Test 9: Complete Flood Label Pipeline"""
    print("\n" + "="*60)
    print("TEST 9: Complete Flood Label Pipeline")
    print("="*60)
    
    start_date = datetime(2024, 6, 1)
    end_date = datetime(2024, 6, 3)
    
    print(f"\nRunning complete pipeline: fetch -> clean -> label")
    
    df = fetch_and_label_cwc_data("TEST_STATION", start_date, end_date, clean=True)
    
    print(f"\n[OK] Pipeline complete: {len(df)} rows")
    print(f"\nFinal Schema:")
    print(f"  Columns: {list(df.columns)}")
    
    # Verify ML-ready format
    required_cols = ['timestamp', 'station_id', 'water_level', 'label', 'quality_flag']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    print(f"\nSample ML-Ready Data:")
    print(df[['timestamp', 'station_id', 'water_level', 'label', 'lead_time_hours', 'quality_flag']].head(10))
    
    print("\n[PASS] Complete flood label pipeline")


def main():
    """Run all tests"""
    print("="*60)
    print("GROUND TRUTH INGESTION TEST SUITE")
    print("="*60)
    
    try:
        # Test 1-3: Signal Cleaning
        test_gauge_validation()
        test_anomaly_detection()
        test_timeseries_cleaning()
        
        # Test 4-5: CWC Scraping & Labeling
        gauge_df = test_cwc_scraping()
        test_flood_label_generation(gauge_df)
        
        # Test 6-8: Landslide Ingestion
        test_landslide_ingestion()
        test_date_parsing()
        test_coordinate_validation()
        
        # Test 9: Complete Pipeline
        test_complete_pipeline()
        
        # Summary
        print("\n" + "="*60)
        print("[PASS] ALL TESTS PASSED")
        print("="*60)
        
        print("\nKey Validations:")
        print("  [OK] Time-series cleaning with physical validation")
        print("  [OK] Gap handling (interpolate short, flag long)")
        print("  [OK] CWC flood gauge scraping (mock data)")
        print("  [OK] Flood label generation (binary + lead time + events)")
        print("  [OK] Landslide inventory ingestion (custom CSV)")
        print("  [OK] Date parsing and coordinate validation")
        print("  [OK] Complete ML-ready pipeline")
        
        print("\nML-Ready Output Schemas:")
        print("\n1. Flood Labels:")
        print("   timestamp | station_id | water_level | warning_level | danger_level |")
        print("   label | lead_time_hours | event_id | quality_flag")
        
        print("\n2. Landslide Inventory:")
        print("   timestamp | lat | lon | event_type | source | location_name")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
