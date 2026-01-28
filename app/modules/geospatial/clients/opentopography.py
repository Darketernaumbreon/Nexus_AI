"""
OpenTopography DEM Acquisition Client

Fetches Digital Elevation Models from OpenTopography API with local caching.
Supports both flood forecasting and landslide risk analysis.

Datasets:
- COP30: Copernicus 30m Global DEM
- SRTMGL1: SRTM 30m Global DEM

Author: NEXUS-AI Team
"""

import hashlib
import time
from pathlib import Path
from typing import Tuple
import requests

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("opentopography")

# OpenTopography API endpoint
OPENTOPOGRAPHY_API_URL = "https://portal.opentopography.org/API/globaldem"

# Dataset mapping
DATASET_CODES = {
    "COP30": "COP30",
    "SRTM": "SRTMGL1",
    "SRTMGL1": "SRTMGL1"
}


def fetch_dem(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    dataset: str = None,
    buffer: float = None
) -> Path:
    """
    Fetch DEM from OpenTopography with local caching.
    
    Args:
        min_lat: Minimum latitude (south)
        min_lon: Minimum longitude (west)
        max_lat: Maximum latitude (north)
        max_lon: Maximum longitude (east)
        dataset: Dataset name (COP30, SRTM, SRTMGL1). Defaults to config.
        buffer: Bounding box buffer in degrees. Defaults to config.
    
    Returns:
        Path to cached DEM GeoTIFF
    
    Raises:
        ValueError: Invalid bounding box or missing API key
        RuntimeError: API request failed
    
    Example:
        >>> dem_path = fetch_dem(26.0, 91.0, 26.5, 91.5, dataset="COP30")
        >>> print(dem_path)
        data/dem_cache/dem_COP30_a1b2c3d4.tif
    """
    # Validate inputs
    if min_lat >= max_lat:
        raise ValueError(f"Invalid latitude range: min_lat ({min_lat}) >= max_lat ({max_lat})")
    if min_lon >= max_lon:
        raise ValueError(f"Invalid longitude range: min_lon ({min_lon}) >= max_lon ({max_lon})")
    
    if not settings.OPENTOPOGRAPHY_API_KEY:
        raise ValueError("OPENTOPOGRAPHY_API_KEY not configured")
    
    # Use defaults from config
    dataset = dataset or settings.DEM_DEFAULT_DATASET
    buffer = buffer if buffer is not None else settings.DEM_BBOX_BUFFER
    
    # Normalize dataset name
    if dataset not in DATASET_CODES:
        raise ValueError(f"Unknown dataset: {dataset}. Valid options: {list(DATASET_CODES.keys())}")
    dataset_code = DATASET_CODES[dataset]
    
    # Apply buffer to bounding box
    buffered_bbox = (
        min_lat - buffer,
        min_lon - buffer,
        max_lat + buffer,
        max_lon + buffer
    )
    
    logger.info(
        "fetch_dem_requested",
        original_bbox=(min_lat, min_lon, max_lat, max_lon),
        buffered_bbox=buffered_bbox,
        dataset=dataset_code,
        buffer=buffer
    )
    
    # Generate cache key and path
    cache_key = _generate_cache_key(buffered_bbox, dataset_code)
    cache_dir = Path(settings.DEM_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    cache_path = cache_dir / f"dem_{dataset_code}_{cache_key}.tif"
    
    # Check cache
    if cache_path.exists():
        logger.info("cache_hit", path=str(cache_path))
        
        # Validate cached DEM
        from app.modules.geospatial.utils.raster_validation import validate_dem
        validation = validate_dem(cache_path)
        
        if validation["valid"]:
            logger.info("cached_dem_valid", metadata=validation)
            return cache_path
        else:
            logger.warning("cached_dem_invalid_redownloading", metadata=validation)
            cache_path.unlink()  # Delete invalid cache
    
    # Cache miss - download DEM
    logger.info("cache_miss_downloading", path=str(cache_path))
    _download_dem(buffered_bbox, dataset_code, cache_path)
    
    # Validate downloaded DEM
    from app.modules.geospatial.utils.raster_validation import validate_dem
    validation = validate_dem(cache_path)
    
    if not validation["valid"]:
        logger.error("downloaded_dem_invalid", metadata=validation)
        raise RuntimeError(f"Downloaded DEM failed validation: {validation}")
    
    logger.info("dem_acquired_successfully", path=str(cache_path), metadata=validation)
    return cache_path


def _generate_cache_key(bbox: Tuple[float, float, float, float], dataset: str) -> str:
    """
    Generate deterministic cache key from bbox and dataset.
    
    Args:
        bbox: (min_lat, min_lon, max_lat, max_lon)
        dataset: Dataset code
    
    Returns:
        8-character hash string
    """
    # Create deterministic string from inputs
    key_string = f"{dataset}_{bbox[0]:.6f}_{bbox[1]:.6f}_{bbox[2]:.6f}_{bbox[3]:.6f}"
    
    # Generate SHA256 hash and truncate
    hash_obj = hashlib.sha256(key_string.encode())
    return hash_obj.hexdigest()[:8]


def _download_dem(
    bbox: Tuple[float, float, float, float],
    dataset: str,
    output_path: Path,
    max_retries: int = 3
) -> None:
    """
    Download DEM from OpenTopography API.
    
    Args:
        bbox: (min_lat, min_lon, max_lat, max_lon)
        dataset: Dataset code (COP30, SRTMGL1)
        output_path: Where to save the GeoTIFF
        max_retries: Maximum retry attempts
    
    Raises:
        RuntimeError: API request failed after retries
    """
    min_lat, min_lon, max_lat, max_lon = bbox
    
    params = {
        "demtype": dataset,
        "south": min_lat,
        "north": max_lat,
        "west": min_lon,
        "east": max_lon,
        "outputFormat": "GTiff",
        "API_Key": settings.OPENTOPOGRAPHY_API_KEY
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "api_request_attempt",
                attempt=attempt,
                url=OPENTOPOGRAPHY_API_URL,
                params={k: v for k, v in params.items() if k != "API_Key"}
            )
            
            response = requests.get(
                OPENTOPOGRAPHY_API_URL,
                params=params,
                timeout=300,  # 5 minutes for large DEMs
                stream=True
            )
            
            # Check response status
            if response.status_code == 200:
                # Save to file
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size_mb = output_path.stat().st_size / 1024 / 1024
                logger.info(
                    "download_successful",
                    path=str(output_path),
                    size_mb=round(file_size_mb, 2)
                )
                return
            
            elif response.status_code == 429:
                # Rate limit - wait and retry
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    "rate_limit_hit_retrying",
                    attempt=attempt,
                    wait_seconds=wait_time
                )
                time.sleep(wait_time)
                continue
            
            else:
                # Other error
                logger.error(
                    "api_error",
                    status_code=response.status_code,
                    response_text=response.text[:500]
                )
                
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise RuntimeError(
                        f"OpenTopography API failed: {response.status_code} - {response.text[:200]}"
                    )
        
        except requests.exceptions.Timeout:
            logger.warning("request_timeout", attempt=attempt)
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            else:
                raise RuntimeError("OpenTopography API timeout after retries")
        
        except requests.exceptions.RequestException as e:
            logger.error("request_exception", attempt=attempt, error=str(e))
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            else:
                raise RuntimeError(f"OpenTopography API request failed: {e}")
    
    raise RuntimeError("Failed to download DEM after all retries")
