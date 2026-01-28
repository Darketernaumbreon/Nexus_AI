"""
Flood Inference Service

Orchestrates flood prediction from raw inputs to response.
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

from app.services.feature_builder import build_flood_features
from app.services.risk_engine import (
    classify_risk,
    get_confidence,
    estimate_lead_time,
    RiskLevel,
    ConfidenceLevel
)
from app.core.logging import get_logger

logger = get_logger("flood_inference")


def get_top_shap_drivers(
    shap_values: np.ndarray,
    feature_names: List[str],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract top-K features driving the prediction.
    
    Performance Note:
        Only returns top-K to keep latency < 20ms.
        Full SHAP is expensive; this is production-grade.
    
    Args:
        shap_values: SHAP values for single prediction
        feature_names: Feature names
        top_k: Number of top drivers to return
    
    Returns:
        List of dicts with feature name and impact
    """
    # Get absolute importance
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


def predict_flood(
    request: Request,
    station_id: str
) -> Dict[str, Any]:
    """
    Predict flood risk for a given station.
    
    Args:
        request: FastAPI request (for app.state access)
        station_id: CWC gauge station ID
    
    Returns:
        Dict with prediction results
    
    Response Schema:
        {
            "hazard": "flood",
            "station_id": "XYZ",
            "probability": 0.72,
            "risk_level": "HIGH",
            "lead_time_hours": 18,
            "top_drivers": [...],
            "confidence": "HIGH",
            "timestamp": "..."
        }
    """
    logger.info("predict_flood_start", station_id=station_id)
    
    # Get model from app state
    ml_models = request.app.state.ml_models
    flood_model = ml_models.get("flood")
    
    if flood_model is None:
        logger.error("flood_model_not_loaded")
        return {
            "hazard": "flood",
            "station_id": station_id,
            "error": "Flood model not available",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    model = flood_model["model"]
    explainer = flood_model["explainer"]
    features = flood_model["features"]
    thresholds = flood_model["thresholds"]
    
    # Build features (Latency: ~250ms)
    X = build_flood_features(
        station_id=station_id,
        timestamp=datetime.utcnow(),
        expected_features=features
    )
    
    # Model inference (Latency: ~5ms)
    probability = model.predict_proba(X)[0][1]
    
    logger.info(
        "flood_prediction_complete",
        station_id=station_id,
        probability=round(probability, 4)
    )
    
    # Risk classification
    risk_level = classify_risk(probability)
    
    # Lead time estimation
    lead_time = estimate_lead_time(probability)
    
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
        "hazard": "flood",
        "station_id": station_id,
        "probability": round(float(probability), 4),
        "risk_level": risk_level.value,
        "lead_time_hours": lead_time,
        "top_drivers": top_drivers,
        "confidence": confidence.value,
        "threshold_used": thresholds.get("optimal_threshold", 0.5),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(
        "flood_response_ready",
        station_id=station_id,
        risk_level=risk_level.value
    )
    
    return response
