"""
Landslide Inference Service

Orchestrates landslide susceptibility prediction from raw inputs to response.
Uses pre-loaded models from app.state.

Latency Budget:
    - Feature build: <= 250ms
    - Model inference: <= 5ms
    - SHAP explanation (top-5): <= 20ms
    - Total: <= 300ms

Author: NEXUS-AI Team
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

from fastapi import Request

from app.services.feature_builder import build_landslide_features
from app.services.risk_engine import (
    classify_risk,
    get_confidence,
    RiskLevel,
    ConfidenceLevel
)
from app.core.logging import get_logger

logger = get_logger("landslide_inference")


def get_top_shap_drivers(
    shap_values: np.ndarray,
    feature_names: List[str],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract top-K features driving the prediction.
    
    Args:
        shap_values: SHAP values for single prediction
        feature_names: Feature names
        top_k: Number of top drivers to return
    
    Returns:
        List of dicts with feature name and impact
    """
    abs_values = np.abs(shap_values)
    top_indices = np.argsort(abs_values)[-top_k:][::-1]
    
    drivers = []
    for idx in top_indices:
        impact = shap_values[idx]
        drivers.append({
            "feature": feature_names[idx],
            "impact": f"{'+' if impact >= 0 else ''}{impact:.3f}"
        })
    
    return drivers


def predict_landslide(
    request: Request,
    lat: float,
    lon: float
) -> Dict[str, Any]:
    """
    Predict landslide susceptibility for a given location.
    
    Args:
        request: FastAPI request (for app.state access)
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dict with prediction results
    
    Response Schema:
        {
            "hazard": "landslide",
            "location": {"lat": ..., "lon": ...},
            "susceptibility": 0.64,
            "risk_level": "MEDIUM",
            "top_drivers": [...],
            "confidence": "MODERATE",
            "timestamp": "..."
        }
    """
    logger.info("predict_landslide_start", lat=lat, lon=lon)
    
    # Get model from app state
    ml_models = request.app.state.ml_models
    landslide_model = ml_models.get("landslide")
    
    if landslide_model is None:
        logger.error("landslide_model_not_loaded")
        return {
            "hazard": "landslide",
            "location": {"lat": lat, "lon": lon},
            "error": "Landslide model not available",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    model = landslide_model["model"]
    explainer = landslide_model["explainer"]
    features = landslide_model["features"]
    thresholds = landslide_model["thresholds"]
    
    # Build features (Latency: ~250ms)
    X = build_landslide_features(
        lat=lat,
        lon=lon,
        date=datetime.utcnow(),
        expected_features=features
    )
    
    # Model inference (Latency: ~5ms)
    susceptibility = model.predict_proba(X)[0][1]
    
    logger.info(
        "landslide_prediction_complete",
        lat=lat,
        lon=lon,
        susceptibility=round(susceptibility, 4)
    )
    
    # Risk classification
    risk_level = classify_risk(susceptibility)
    
    # SHAP explanation (Latency: ~20ms, top-5 only)
    shap_values = explainer.shap_values(X)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # For binary classification
    
    top_drivers = get_top_shap_drivers(
        shap_values[0],
        features,
        top_k=5
    )
    
    # Confidence
    confidence = get_confidence(data_quality="good", weather_cached=True)
    
    response = {
        "hazard": "landslide",
        "location": {"lat": lat, "lon": lon},
        "susceptibility": round(float(susceptibility), 4),
        "risk_level": risk_level.value,
        "top_drivers": top_drivers,
        "confidence": confidence.value,
        "threshold_used": thresholds.get("optimal_threshold", 0.5),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(
        "landslide_response_ready",
        lat=lat,
        lon=lon,
        risk_level=risk_level.value
    )
    
    return response
