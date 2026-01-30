"""
XGBoost Training Pipeline for Flood Prediction

Trains binary classifier with recall optimization and class imbalance handling.

Author: NEXUS-AI Team
"""

from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import pickle
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import xgboost as xgb

from app.core.config import settings
from app.core.logging import get_logger
from ml_engine.training.feature_engineering import get_feature_columns

logger = get_logger("train_xgb")


def prepare_train_test_split(
    df: pd.DataFrame,
    test_size: Optional[float] = None,
    method: str = 'time_series'
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, list]:
    """
    Split datset into train and test sets.
    
    Args:
        df: Dataset with engineered features
        test_size: Fraction for test set (default from config)
        method: Split method ('time_series' or 'random')
    
    Returns:
        X_train, X_test, y_train, y_test, feature_names
    
    Example:
        >>> X_tr, X_te, y_tr, y_te, features = prepare_train_test_split(df)
    """
    if test_size is None:
        test_size = settings.TEST_SIZE
    
    logger.info(
        "preparing_train_test_split",
        total_rows=len(df),
        test_size=test_size,
        method=method
    )
    
    # Get feature columns
    feature_cols = get_feature_columns(df)
    
    # Target is 'label'
    X = df[feature_cols]
    y = df['label']
    
    if method == 'time_series':
        # Walk-forward split: train on earlier data, test on later
        # This prevents data leakage
        split_idx = int(len(df) * (1 - test_size))
        
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]
        
        logger.info(
            "time_series_split",
            train_start=df['timestamp'].iloc[0],
            train_end=df['timestamp'].iloc[split_idx-1],
            test_start=df['timestamp'].iloc[split_idx],
            test_end=df['timestamp'].iloc[-1]
        )
    
    elif method == 'random':
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y
        )
        logger.info("random_split", stratified=True)
    
    else:
        raise ValueError(f"Unknown split method: {method}")
    
    # Log class distribution
    train_pos = y_train.sum()
    train_neg = len(y_train) - train_pos
    test_pos = y_test.sum()
    test_neg = len(y_test) - test_pos
    
    logger.info(
        "class_distribution",
        train_positive=int(train_pos),
        train_negative=int(train_neg),
        train_ratio=round(train_pos / len(y_train), 3),
        test_positive=int(test_pos),
        test_negative=int(test_neg),
        test_ratio=round(test_pos / len(y_test), 3)
    )
    
    return X_train, X_test, y_train, y_test, feature_cols


def train_xgboost_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: Optional[pd.DataFrame] = None,
    y_val: Optional[pd.Series] = None,
    params: Optional[Dict[str, Any]] = None
) -> xgb.XGBClassifier:
    """
    Train XGBoost binary classifier with recall optimization.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Optional validation features (for early stopping)
        y_val: Optional validation labels
        params: Optional custom hyperparameters
    
    Returns:
        Trained XGBoost model
    
    Example:
        >>> model = train_xgboost_model(X_train, y_train, X_val, y_val)
    """
    logger.info("training_xgboost_model", train_samples=len(X_train))
    
    # Default hyperparameters (conservative for stability)
    if params is None:
        params = {
            'max_depth': settings.XGB_MAX_DEPTH,
            'learning_rate': settings.XGB_LEARNING_RATE,
            'n_estimators': settings.XGB_N_ESTIMATORS,
            'subsample': settings.XGB_SUBSAMPLE,
            'colsample_bytree': settings.XGB_COLSAMPLE_BYTREE,
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42,
            'n_jobs': -1
        }
    
    # Handle class imbalance
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    
    params['scale_pos_weight'] = scale_pos_weight
    
    logger.info(
        "class_imbalance_handling",
        positive_samples=int(pos_count),
        negative_samples=int(neg_count),
        scale_pos_weight=round(scale_pos_weight, 2)
    )
    
    # Initialize model
    model = xgb.XGBClassifier(**params)
    
    # Prepare evaluation set for early stopping
    eval_set = []
    if X_val is not None and y_val is not None:
        eval_set = [(X_val, y_val)]
    
    # Train
    if eval_set:
        model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )
        logger.info("training_complete_with_early_stopping")
    else:
        model.fit(X_train, y_train, verbose=False)
        logger.info("training_complete")
    
    # Log feature importance
    feature_importance = dict(zip(X_train.columns, model.feature_importances_))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    
    logger.info(
        "top_features",
        features={k: round(v, 4) for k, v in top_features}
    )
    
    return model


def save_model_artifacts(
    model: xgb.XGBClassifier,
    feature_names: list,
    output_dir: Optional[str] = None,
    thresholds: Optional[Dict[str, float]] = None
) -> None:
    """
    Save trained model and metadata artifacts.
    
    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        output_dir: Directory to save artifacts (default from config)
        thresholds: Optional decision thresholds dict
    
    Creates:
        - xgb_model.pkl: Trained model
        - feature_list.json: Feature names and importance
        - thresholds.json: Decision thresholds (if provided)
    """
    if output_dir is None:
        output_dir = settings.ML_ARTIFACTS_DIR
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Save model
    model_path = output_path / "xgb_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info("model_saved", path=str(model_path))
    
    # 2. Save feature metadata
    feature_importance = dict(zip(feature_names, model.feature_importances_))
    feature_metadata = {
        "features": feature_names,
        "feature_importance": {k: float(v) for k, v in feature_importance.items()},
        "num_features": len(feature_names)
    }
    
    features_path = output_path / "feature_list.json"
    with open(features_path, 'w') as f:
        json.dump(feature_metadata, f, indent=2)
    logger.info("features_saved", path=str(features_path), num_features=len(feature_names))
    
    # 3. Save thresholds if provided
    if thresholds:
        thresholds_path = output_path / "thresholds.json"
        with open(thresholds_path, 'w') as f:
            json.dump(thresholds, f, indent=2)
        logger.info("thresholds_saved", path=str(thresholds_path))


def load_model_artifacts(
    artifact_dir: Optional[str] = None
) -> Tuple[xgb.XGBClassifier, list, Optional[Dict]]:
    """
    Load trained model and metadata artifacts.
    
    Args:
        artifact_dir: Directory containing artifacts (default from config)
    
    Returns:
        model, feature_names, thresholds
    """
    if artifact_dir is None:
        artifact_dir = settings.ML_ARTIFACTS_DIR
    
    artifact_path = Path(artifact_dir)
    
    # Load model
    model_path = artifact_path / "xgb_model.pkl"
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info("model_loaded", path=str(model_path))
    
    # Load features
    features_path = artifact_path / "feature_list.json"
    with open(features_path, 'r') as f:
        feature_metadata = json.load(f)
    feature_names = feature_metadata['features']
    logger.info("features_loaded", num_features=len(feature_names))
    
    # Load thresholds if exists
    thresholds = None
    thresholds_path = artifact_path / "thresholds.json"
    if thresholds_path.exists():
        with open(thresholds_path, 'r') as f:
            thresholds = json.load(f)
        logger.info("thresholds_loaded")
    
    return model, feature_names, thresholds
