"""
Model Lifespan Manager

Loads ML models ONCE at FastAPI startup.
Models are stored in app.state.ml_models with explicit structure.

Author: NEXUS-AI Team
"""

import json
import pickle
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any

import shap
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("lifespan")


def load_flood_model() -> Dict[str, Any]:
    """
    Load flood prediction model and associated artifacts.
    
    Returns:
        Dict with keys: model, explainer, features, thresholds
    
    Latency Budget:
        - Model load: ~100ms (disk I/O)
        - SHAP explainer init: ~50ms
    """
    artifacts_dir = Path(settings.ML_ARTIFACTS_DIR)
    
    # Load model
    model_path = artifacts_dir / "xgb_model.pkl"
    if not model_path.exists():
        logger.warning("flood_model_not_found", path=str(model_path))
        return None
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info("flood_model_loaded", path=str(model_path))
    
    # Load feature list
    features_path = artifacts_dir / "feature_list.json"
    with open(features_path, 'r') as f:
        features_data = json.load(f)
    
    features = features_data.get("features", [])
    logger.info("flood_features_loaded", count=len(features))
    
    # Load thresholds
    thresholds_path = artifacts_dir / "thresholds.json"
    with open(thresholds_path, 'r') as f:
        thresholds = json.load(f)
    
    logger.info("flood_thresholds_loaded", threshold=thresholds.get("optimal_threshold"))
    
    # Initialize SHAP explainer (TreeExplainer is fast for XGBoost)
    explainer = shap.TreeExplainer(model)
    logger.info("flood_shap_explainer_initialized")
    
    return {
        "model": model,
        "explainer": explainer,
        "features": features,
        "thresholds": thresholds
    }


def load_landslide_model() -> Dict[str, Any]:
    """
    Load landslide prediction model and associated artifacts.
    
    Returns:
        Dict with keys: model, explainer, features, thresholds
    """
    artifacts_dir = Path(settings.ML_ARTIFACTS_DIR) / "landslide"
    
    # Load model
    model_path = artifacts_dir / "xgb_model_landslide.pkl"
    if not model_path.exists():
        logger.warning("landslide_model_not_found", path=str(model_path))
        return None
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info("landslide_model_loaded", path=str(model_path))
    
    # Load feature list
    features_path = artifacts_dir / "feature_list.json"
    with open(features_path, 'r') as f:
        features_data = json.load(f)
    
    features = features_data.get("features", [])
    logger.info("landslide_features_loaded", count=len(features))
    
    # Load thresholds
    thresholds_path = artifacts_dir / "thresholds.json"
    with open(thresholds_path, 'r') as f:
        thresholds = json.load(f)
    
    logger.info("landslide_thresholds_loaded", threshold=thresholds.get("optimal_threshold"))
    
    # Initialize SHAP explainer
    explainer = shap.TreeExplainer(model)
    logger.info("landslide_shap_explainer_initialized")
    
    return {
        "model": model,
        "explainer": explainer,
        "features": features,
        "thresholds": thresholds
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    
    Startup:
        - Load flood model
        - Load landslide model
        - Initialize SHAP explainers
        - Store in app.state.ml_models
    
    Shutdown:
        - Cleanup (if needed)
    """
    logger.info("startup_loading_models")
    
    # Structured model storage (as per hardening notes)
    app.state.ml_models = {
        "flood": None,
        "landslide": None
    }
    
    # Load flood model
    try:
        flood_artifacts = load_flood_model()
        if flood_artifacts:
            app.state.ml_models["flood"] = flood_artifacts
            logger.info("flood_model_ready")
        else:
            logger.warning("flood_model_unavailable")
    except Exception as e:
        logger.error("flood_model_load_failed", error=str(e))
    
    # Load landslide model
    try:
        landslide_artifacts = load_landslide_model()
        if landslide_artifacts:
            app.state.ml_models["landslide"] = landslide_artifacts
            logger.info("landslide_model_ready")
        else:
            logger.warning("landslide_model_unavailable")
    except Exception as e:
        logger.error("landslide_model_load_failed", error=str(e))
    
    # Summary
    models_loaded = sum(1 for v in app.state.ml_models.values() if v is not None)
    logger.info(
        "startup_complete",
        models_loaded=models_loaded,
        total_models=len(app.state.ml_models)
    )
    
    yield  # App runs here
    
    # Shutdown
    logger.info("shutdown_cleanup")
    app.state.ml_models = None
