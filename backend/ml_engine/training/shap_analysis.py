"""
SHAP Explainability Analysis for Flood Prediction

Generates SHAP values for model interpretability (MANDATORY for government use).

Author: NEXUS-AI Team
"""

from typing import Optional, List, Tuple, Dict
from pathlib import Path
import pickle
import pandas as pd
import numpy as np
import shap
import xgboost as xgb

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("shap_analysis")


def compute_shap_values(
    model: xgb.XGBClassifier,
    X_background: pd.DataFrame,
    X_explain: Optional[pd.DataFrame] = None
) -> Tuple[shap.Explanation, shap.TreeExplainer]:
    """
    Compute SHAP values for model predictions.
    
    Args:
        model: Trained XGBoost model
        X_background: Background dataset for TreeExplainer (sample of training data)
        X_explain: Data to explain (default: use background)
    
    Returns:
        (shap_values, explainer)
    
    Example:
        >>> shap_values, explainer = compute_shap_values(model, X_train.sample(100), X_test)
    """
    if X_explain is None:
        X_explain = X_background
    
    logger.info(
        "computing_shap_values",
        background_size=len(X_background),
        explain_size=len(X_explain)
    )
    
    # Create TreeExplainer (fast for XGBoost)
    explainer = shap.TreeExplainer(model, X_background)
    
    # Compute SHAP values
    shap_values = explainer(X_explain)
    
    logger.info("shap_values_computed", shape=shap_values.values.shape)
    
    return shap_values, explainer


def get_top_drivers(
    shap_values: shap.Explanation,
    X: pd.DataFrame,
    top_k: int = 5
) -> pd.DataFrame:
    """
    Get top K contributing features for each prediction.
    
    Args:
        shap_values: Computed SHAP values
        X: Feature data
        top_k: Number of top features to return
    
    Returns:
        DataFrame with top features and their contributions
    
    Example:
        >>> top_features = get_top_drivers(shap_values, X_test, top_k=3)
        >>> print(top_features.head())
    """
    logger.info("extracting_top_drivers", top_k=top_k)
    
    results = []
    
    for i in range(len(X)):
        # Get absolute SHAP values for this prediction
        abs_shap = np.abs(shap_values.values[i])
        
        # Get top K indices
        top_indices = np.argsort(abs_shap)[-top_k:][::-1]
        
        # Build result row
        row = {'sample_idx': i}
        for rank, idx in enumerate(top_indices, 1):
            feature_name = X.columns[idx]
            shap_value = shap_values.values[i, idx]
            feature_value = X.iloc[i, idx]
            
            row[f'top{rank}_feature'] = feature_name
            row[f'top{rank}_shap'] = shap_value
            row[f'top{rank}_value'] = feature_value
        
        results.append(row)
    
    df_drivers = pd.DataFrame(results)
    
    logger.info("top_drivers_extracted", samples=len(df_drivers))
    
    return df_drivers


def save_shap_artifacts(
    shap_values: shap.Explanation,
    output_dir: Optional[str] = None
) -> None:
    """
    Save SHAP values to artifacts directory.
    
    Args:
        shap_values: Computed SHAP values
        output_dir: Directory to save (default from config)
    """
    if output_dir is None:
        output_dir = settings.ML_ARTIFACTS_DIR
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save SHAP values
    shap_path = output_path / "shap_values.pkl"
    with open(shap_path, 'wb') as f:
        pickle.dump(shap_values, f)
    
    logger.info("shap_values_saved", path=str(shap_path))


def load_shap_artifacts(
    artifact_dir: Optional[str] = None
) -> shap.Explanation:
    """
    Load SHAP values from artifacts.
    
    Args:
        artifact_dir: Directory containing SHAP artifacts
    
    Returns:
        Loaded SHAP values
    """
    if artifact_dir is None:
        artifact_dir = settings.ML_ARTIFACTS_DIR
    
    shap_path = Path(artifact_dir) / "shap_values.pkl"
    
    with open(shap_path, 'rb') as f:
        shap_values = pickle.load(f)
    
    logger.info("shap_values_loaded", path=str(shap_path))
    
    return shap_values


def explain_prediction(
    model: xgb.XGBClassifier,
    explainer: shap.TreeExplainer,
    X_single: pd.DataFrame,
    feature_names: List[str]
) -> Dict[str, float]:
    """
    Explain a single prediction.
    
    Args:
        model: Trained model
        explainer: SHAP explainer
        X_single: Single row DataFrame (one prediction)
        feature_names: List of feature names
    
    Returns:
        Dictionary mapping feature names to SHAP contributions
    """
    shap_values = explainer(X_single)
    
    contributions = {}
    for i, feature in enumerate(feature_names):
        contributions[feature] = float(shap_values.values[0, i])
    
    # Sort by absolute contribution
    contributions = dict(sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True))
    
    return contributions
