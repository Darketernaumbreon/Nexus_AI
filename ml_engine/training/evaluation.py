"""
Model Evaluation for Flood Prediction

Comprehensive evaluation with flood-specific metrics and threshold optimization.

Author: NEXUS-AI Team
"""

from typing import Tuple, Dict, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, fbeta_score
)
import xgboost as xgb

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("evaluation")


def evaluate_model(
    model: xgb.XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    Comprehensive model evaluation with flood-specific metrics.
    
    Args:
        model: Trained XGBoost model
        X_test: Test features
        y_test: Test labels
        threshold: Decision threshold for binary classification
   
    Returns:
        Dictionary of evaluation metrics
    
    Example:
        >>> metrics = evaluate_model(model, X_test, y_test, threshold=0.35)
        >>> print(f"Recall: {metrics['recall']:.3f}")
    """
    logger.info("evaluating_model", test_samples=len(X_test), threshold=threshold)
    
    # Get predictions
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    # Metrics
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    f2 = fbeta_score(y_test, y_pred, beta=2.0, zero_division=0)  # Recall-focused
    
    # ROC-AUC and PR-AUC
    roc_auc = roc_auc_score(y_test, y_proba)
    pr_auc = average_precision_score(y_test, y_proba)
    
    metrics = {
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'true_positives': int(tp),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'f2_score': float(f2),
        'roc_auc': float(roc_auc),
        'pr_auc': float(pr_auc),
        'threshold': float(threshold)
    }
    
    logger.info(
        "evaluation_complete",
        recall=round(recall, 3),
        precision=round(precision, 3),
        f2_score=round(f2, 3),
        roc_auc=round(roc_auc, 3)
    )
    
    logger.info(
        "confusion_matrix",
        TP=int(tp),
        FP=int(fp),
        TN=int(tn),
        FN=int(fn)
    )
    
    return metrics


def find_optimal_threshold(
    model: xgb.XGBClassifier,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    metric: str = 'f2'
) -> Tuple[float, float]:
    """
    Find optimal decision threshold by sweeping thresholds.
    
    Args:
        model: Trained XGBoost model
        X_val: Validation features
        y_val: Validation labels
        metric: Metric to optimize ('f1', 'f2', 'recall')
    
    Returns:
        (optimal_threshold, best_score)
    
    Example:
        >>> threshold, score = find_optimal_threshold(model, X_val, y_val, metric='f2')
        >>> print(f"Optimal threshold: {threshold:.2f}, F2: {score:.3f}")
    """
    logger.info("finding_optimal_threshold", metric=metric)
    
    # Get probabilities
    y_proba = model.predict_proba(X_val)[:, 1]
    
    # Try thresholds from 0.1 to 0.9
    thresholds = np.arange(0.1, 0.95, 0.05)
    scores = []
    
    for threshold in thresholds:
        y_pred = (y_proba >= threshold).astype(int)
        
        if metric == 'f1':
            score = f1_score(y_val, y_pred, zero_division=0)
        elif metric == 'f2':
            score = fbeta_score(y_val, y_pred, beta=2.0, zero_division=0)
        elif metric == 'recall':
            score = recall_score(y_val, y_pred, zero_division=0)
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        scores.append(score)
    
    # Find best threshold
    best_idx = np.argmax(scores)
    optimal_threshold = thresholds[best_idx]
    best_score = scores[best_idx]
    
    logger.info(
        "optimal_threshold_found",
        threshold=round(optimal_threshold, 2),
        score=round(best_score, 3),
        metric=metric
    )
    
    return float(optimal_threshold), float(best_score)


def compute_lead_time_analysis(
    df: pd.DataFrame,
    predictions: np.ndarray,
    probabilities: np.ndarray
) -> Dict[str, float]:
    """
   Analyze how early the model can predict floods.
    
    Args:
        df: Test dataset with 'lead_time_hours' column
        predictions: Binary predictions
        probabilities: Prediction probabilities
    
    Returns:
        Dictionary with lead time statistics
    """
    if 'lead_time_hours' not in df.columns:
        logger.warning("no_lead_time_column")
        return {}
    
    # Get correct predictions where true label = 1
    true_floods = df['label'] == 1
    correct_preds = (predictions == 1) & true_floods
    
    if not correct_preds.any():
        logger.warning("no_correct_flood_predictions")
        return {}
    
    # Lead times for correct predictions
    lead_times = df.loc[correct_preds, 'lead_time_hours'].dropna()
    
    if len(lead_times) == 0:
        return {}
    
    lead_time_stats = {
        'mean_lead_time_hours': float(lead_times.mean()),
        'median_lead_time_hours': float(lead_times.median()),
        'min_lead_time_hours': float(lead_times.min()),
        'max_lead_time_hours': float(lead_times.max())
    }
    
    logger.info(
        "lead_time_analysis",
        mean_hours=round(lead_time_stats['mean_lead_time_hours'], 1),
        median_hours=round(lead_time_stats['median_lead_time_hours'], 1)
    )
    
    return lead_time_stats
