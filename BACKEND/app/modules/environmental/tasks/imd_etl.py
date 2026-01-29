"""
IMD Rainfall ETL Pipeline

Fetches gridded rainfall data from the Indian Meteorological Department (IMD)
using the `imdlib` library. This provides authoritative "Ground Truth" data
for the Indian region.

Author: NEXUS-AI Team
"""

import imdlib as imd
import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("imd_etl")

def fetch_imd_rainfall(
    start_date: date,
    end_date: date,
    lat_range: tuple[float, float] = (24.0, 30.0), # Approx North East
    lon_range: tuple[float, float] = (89.0, 97.0)
) -> List[Dict[str, Any]]:
    """
    Fetch gridded rainfall data from IMD.
    
    Args:
        start_date: Start date for data
        end_date: End date for data
        lat_range: (min_lat, max_lat)
        lon_range: (min_lon, max_lon)
        
    Returns:
        List of dicts containing {lat, lon, rainfall_mm, date}
    """
    logger.info("fetching_imd_data", start=start_date, end=end_date)
    
    try:
        # IMD data is usually updated with a delay. 
        # For real-time, we might need a different source or accept lag.
        # imdlib downloads data to local storage.
        data_dir = Path("data/imd_cache")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # imdlib requires start and end year
        start_year = start_date.year
        end_year = end_date.year
        
        imd_data = None
        
        # Try fetching
        try:
             imd_data = imd.get_data("rain", start_year, end_year, fn_format="yearwise", file_dir=str(data_dir))
        except Exception as e:
            logger.warning(f"IMD Fetch failed for {start_year}: {e}. Trying fallback to known available year (2025 - Monsoon).")
            # Fallback for Demo/MVP if real-time data isn't published yet
            try:
                # Try Monsoon 2025 (e.g. July) which should have data if 2026 is missing
                imd_data = imd.get_data("rain", 2025, 2025, fn_format="yearwise", file_dir=str(data_dir))
            except Exception as e2:
                logger.error(f"IMD Fallback failed: {e2}")
                return []
        
        if imd_data is None:
            return []
            
        # Convert to Xarray for easy slicing
        ds = imd_data.get_xarray()
        
        # Slice for our region of interest
        # Be careful with coordinate names in imdlib (lat/lon vs latitude/longitude)
        ds_region = ds.sel(lat=slice(lat_range[0], lat_range[1]), lon=slice(lon_range[0], lon_range[1]))
        
        results = []
        
        # Iterate through the time series
        # Using a simplistic loop for MVP clarity
        times = ds_region.time.values
        lats = ds_region.lat.values
        lons = ds_region.lon.values
        rainfall = ds_region.rain.values # Shape: (time, lat, lon)
        
        # Optimization: Just take the mean or max for a quick "regional status"
        # Or return points. For visualization, points are better.
        
        # Let's extract non-zero rainfall points for the latest available date in range
        if len(times) == 0:
            logger.warning("imd_no_data_found_in_range")
            return []
            
        latest_idx = -1 # Last day
        current_date_obj = pd.to_datetime(times[latest_idx])
        
        # Grid loop
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                val = rainfall[latest_idx, i, j]
                if not np.isnan(val) and val > 0:
                    results.append({
                        "lat": float(lat),
                        "lon": float(lon),
                        "rainfall_mm": float(val),
                        "date": current_date_obj.strftime("%Y-%m-%d"),
                        "source": "IMD"
                    })
                    
        logger.info("imd_fetch_success", points=len(results))
        return results
        
    except Exception as e:
        logger.error("imd_fetch_failed", error=str(e))
        # Fallback to empty list so we don't crash
        return []

if __name__ == "__main__":
    # Test run
    # Use previous year because current year might not be available in public grid yet
    # Adjust as per imdlib capabilities
    test_start = date(2023, 6, 1) 
    test_end = date(2023, 6, 2)
    data = fetch_imd_rainfall(test_start, test_end)
    print(f"Fetched {len(data)} IMD points.")
