"""
Raster Validation Utilities

Validates DEM integrity for flood and landslide modeling.
Checks CRS, resolution, NoData values, and overall quality.

Author: NEXUS-AI Team
"""

from pathlib import Path
from typing import Dict, Optional
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pyproj import CRS, Transformer

from app.core.logging import get_logger

logger = get_logger("raster_validation")

# Validation thresholds
MIN_RESOLUTION_M = 20.0  # meters
MAX_RESOLUTION_M = 40.0  # meters
MAX_VOID_PERCENTAGE = 30.0  # percent
WARN_RESOLUTION_M = 100.0  # warn if coarser than this


def validate_dem(dem_path: Path) -> Dict:
    """
    Validate DEM for flood and landslide modeling.
    
    Checks:
    - CRS (must be EPSG:4326 or convertible)
    - Resolution (~30m expected)
    - NoData handling
    - File integrity
    
    Args:
        dem_path: Path to DEM GeoTIFF
    
    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'crs': str,
            'resolution': float (meters),
            'nodata': float,
            'min_elev': float,
            'max_elev': float,
            'void_pct': float,
            'warnings': list[str]
        }
    
    Example:
        >>> metadata = validate_dem(Path("dem.tif"))
        >>> if metadata['valid']:
        ...     print(f"DEM is valid, resolution: {metadata['resolution']}m")
    """
    warnings = []
    
    try:
        with rasterio.open(dem_path) as src:
            # Check CRS
            crs_str = src.crs.to_string() if src.crs else "UNKNOWN"
            
            if not src.crs:
                logger.error("no_crs_found", path=str(dem_path))
                return {
                    "valid": False,
                    "crs": "UNKNOWN",
                    "resolution": None,
                    "nodata": None,
                    "min_elev": None,
                    "max_elev": None,
                    "void_pct": None,
                    "warnings": ["No CRS found"]
                }
            
            # Check if CRS is WGS84
            is_wgs84 = src.crs.to_epsg() == 4326
            if not is_wgs84:
                warnings.append(f"CRS is {crs_str}, not EPSG:4326 (may need reprojection)")
            
            # Calculate resolution in meters
            resolution_m = _check_resolution(src.transform, src.crs)
            
            if resolution_m < MIN_RESOLUTION_M:
                warnings.append(f"Resolution ({resolution_m:.1f}m) finer than expected (20-40m)")
            elif resolution_m > MAX_RESOLUTION_M:
                if resolution_m > WARN_RESOLUTION_M:
                    warnings.append(f"Resolution ({resolution_m:.1f}m) too coarse (>{WARN_RESOLUTION_M}m)")
                else:
                    warnings.append(f"Resolution ({resolution_m:.1f}m) outside optimal range (20-40m)")
            
            # Check NoData
            nodata = src.nodata
            if nodata is None:
                warnings.append("No NoData value defined")
            
            # Read data and compute statistics
            data = src.read(1)
            
            # Calculate void percentage
            if nodata is not None:
                void_mask = data == nodata
                void_pct = (void_mask.sum() / data.size) * 100
            else:
                void_pct = 0.0
            
            if void_pct > MAX_VOID_PERCENTAGE:
                warnings.append(f"Excessive voids: {void_pct:.1f}% (max {MAX_VOID_PERCENTAGE}%)")
            
            # Calculate elevation statistics (excluding NoData)
            if nodata is not None:
                valid_data = data[data != nodata]
            else:
                valid_data = data
            
            if valid_data.size > 0:
                min_elev = float(valid_data.min())
                max_elev = float(valid_data.max())
            else:
                min_elev = None
                max_elev = None
                warnings.append("No valid elevation data found")
            
            # Determine overall validity
            is_valid = (
                src.crs is not None and
                resolution_m <= WARN_RESOLUTION_M and
                void_pct <= MAX_VOID_PERCENTAGE and
                valid_data.size > 0
            )
            
            result = {
                "valid": is_valid,
                "crs": crs_str,
                "resolution": round(resolution_m, 2),
                "nodata": nodata,
                "min_elev": round(min_elev, 2) if min_elev is not None else None,
                "max_elev": round(max_elev, 2) if max_elev is not None else None,
                "void_pct": round(void_pct, 2),
                "warnings": warnings
            }
            
            logger.info("dem_validation_complete", path=str(dem_path), result=result)
            return result
    
    except Exception as e:
        logger.error("validation_failed", path=str(dem_path), error=str(e))
        return {
            "valid": False,
            "crs": None,
            "resolution": None,
            "nodata": None,
            "min_elev": None,
            "max_elev": None,
            "void_pct": None,
            "warnings": [f"Validation error: {str(e)}"]
        }


def _check_resolution(transform, crs) -> float:
    """
    Calculate ground resolution in meters.
    
    Handles both geographic (degrees) and projected (meters) CRS.
    
    Args:
        transform: Rasterio affine transform
        crs: Rasterio CRS object
    
    Returns:
        Resolution in meters
    """
    # Get pixel size in CRS units
    pixel_size_x = abs(transform.a)
    pixel_size_y = abs(transform.e)
    
    # Average pixel size
    pixel_size = (pixel_size_x + pixel_size_y) / 2
    
    # Check if CRS is geographic (degrees)
    if crs.is_geographic:
        # Convert degrees to meters at equator
        # 1 degree ≈ 111,320 meters at equator
        # For more accuracy, we could use the center latitude
        resolution_m = pixel_size * 111320
    else:
        # Already in meters (or assumed to be)
        resolution_m = pixel_size
    
    return resolution_m


def reproject_to_wgs84(
    dem_path: Path,
    output_path: Optional[Path] = None
) -> Path:
    """
    Reproject DEM to WGS84 (EPSG:4326).
    
    Args:
        dem_path: Input DEM path
        output_path: Output path (if None, creates _wgs84 suffix)
    
    Returns:
        Path to reprojected DEM
    
    Raises:
        RuntimeError: Reprojection failed
    
    Example:
        >>> wgs84_path = reproject_to_wgs84(Path("dem_utm.tif"))
    """
    if output_path is None:
        output_path = dem_path.parent / f"{dem_path.stem}_wgs84.tif"
    
    try:
        with rasterio.open(dem_path) as src:
            # Check if already WGS84
            if src.crs.to_epsg() == 4326:
                logger.info("already_wgs84", path=str(dem_path))
                return dem_path
            
            # Calculate transform for WGS84
            dst_crs = CRS.from_epsg(4326)
            transform, width, height = calculate_default_transform(
                src.crs,
                dst_crs,
                src.width,
                src.height,
                *src.bounds
            )
            
            # Update metadata
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })
            
            # Reproject
            with rasterio.open(output_path, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.bilinear
                    )
            
            logger.info(
                "reprojection_complete",
                input=str(dem_path),
                output=str(output_path),
                src_crs=src.crs.to_string(),
                dst_crs=dst_crs.to_string()
            )
            
            return output_path
    
    except Exception as e:
        logger.error("reprojection_failed", path=str(dem_path), error=str(e))
        raise RuntimeError(f"Failed to reproject DEM: {e}")
