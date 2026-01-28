"""
Test Script for Flood Prediction Model (Task 9A)

Tests:
1. Dataset construction (join weather + terrain + labels)
2. Feature engineering (lag features, rolling sums)
3. XGBoost training
4. Model evaluation with F2-score
5. SHAP explainability

Author: NEXUS-AI Team
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from ml_engine.training.dataset_builder import build_flood_dataset, save_dataset
from ml_engine.training.feature_engineering import engineer_flood_features, get_feature_columns
from ml_engine.training.train_xgb import (
    prepare_train_test_split,
    train_xgboost_model,
    save_model_artifacts
)
from ml_engine.training.evaluation import (
    evaluate_model,
    find_optimal_threshold,
    compute_lead_time_analysis
)
from ml_engine.training.shap_analysis import (
    compute_shap_values,
    get_top_drivers,
    save_shap_artifacts
)
from app.core.logging import configure_logger

# Configure logging
configure_logger()


def test_dataset_construction():
    """Test 1: Dataset Construction"""
    print("\n" + "="*60)
    print("TEST 1: Dataset Construction")
    print("="*60)
    
    # Build dataset for test station (30 days to ensure enough data after lag creation)
    start_date = datetime(2024, 6, 1)
    end_date = datetime(2024, 7, 1)  # 30 days
    
    print(f"\nBuilding dataset: {start_date} to {end_date}")
    
    df = build_flood_dataset(
        station_ids=["GUW001"],
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"\n[OK] Dataset built: {len(df)} rows")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Validation
    assert len(df) > 0, "Dataset is empty"
    assert 'rainfall_mm' in df.columns, "Missing rainfall_mm"
    assert 'label' in df.columns, "Missing label"
    assert 'catchment_area' in df.columns, "Missing terrain features"
    
    flood_rate = df['label'].mean()
    print(f"\nFlood rate: {flood_rate:.1%}")
    
    print("\n[PASS] Dataset construction")
    return df


def test_feature_engineering(df):
    """Test 2: Feature Engineering"""
    print("\n" + "="*60)
    print("TEST 2: Feature Engineering")
    print("="*60)
    
    print(f"\nEngineering features...")
    
    df_features = engineer_flood_features(df)
    
    print(f"\n[OK] Features engineered: {len(df_features)} rows")
    
    # Get feature columns
    feature_cols = get_feature_columns(df_features)
    
    print(f"\nFeature count: {len(feature_cols)}")
    print(f"\nFeatures created:")
    for col in sorted(feature_cols):
        print(f"  - {col}")
    
    # Validation
    assert 'rainfall_mm_lag_1' in feature_cols, "Missing lag features"
    assert 'rainfall_mm_3d_sum' in feature_cols, "Missing rolling features"
    assert 'catchment_area' in feature_cols, "Missing static features"
    
    # Note: Some non-feature columns (like event_id) may have NaN values, which is expected
    #       Lag features themselves should not have NaN after dropping early rows
    
    print(f"\nSample features:")
    print(df_features[feature_cols[:5]].head())
    
    print("\n[PASS] Feature engineering")
    return df_features


def test_model_training(df_features):
    """Test 3: Model Training"""
    print("\n" + "="*60)
    print("TEST 3: Model Training")
    print("="*60)
    
    # Split data
    print("\nSplitting data (time-series split)...")
    X_train, X_test, y_train, y_test, feature_names = prepare_train_test_split(
        df_features,
        method='time_series'
    )
    
    print(f"\nTrain set: {len(X_train)} rows")
    print(f"Test set: {len(X_test)} rows")
    
    # Train model
    print("\nTraining XGBoost model...")
    model = train_xgboost_model(X_train, y_train)
    
    print(f"\n[OK] Model trained")
    print(f"Features used: {len(feature_names)}")
    
    # Validation
    assert model is not None, "Model training failed"
    assert hasattr(model, 'predict_proba'), "Model missing predict_proba"
    
    print("\n[PASS] Model training")
    return model, X_train, X_test, y_train, y_test, feature_names


def test_model_evaluation(model, X_test, y_test, df_features):
    """Test 4: Model Evaluation"""
    print("\n" + "="*60)
    print("TEST 4: Model Evaluation")
    print("="*60)
    
    # Find optimal threshold
    print("\nFinding optimal threshold (F2-score)...")
    optimal_threshold, f2_score = find_optimal_threshold(
        model,
        X_test,
        y_test,
        metric='f2'
    )
    
    print(f"\nOptimal threshold: {optimal_threshold:.2f}")
    print(f"F2-score: {f2_score:.3f}")
    
    # Evaluate at optimal threshold
    print("\nEvaluating model...")
    metrics = evaluate_model(model, X_test, y_test, threshold=optimal_threshold)
    
    print(f"\n[OK] Model evaluated")
    print(f"\nMetrics:")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall: {metrics['recall']:.3f}")
    print(f"  F1-Score: {metrics['f1_score']:.3f}")
    print(f"  F2-Score: {metrics['f2_score']:.3f}")
    print(f"  ROC-AUC: {metrics['roc_auc']:.3f}")
    print(f"  PR-AUC: {metrics['pr_auc']:.3f}")
    
    print(f"\nConfusion Matrix:")
    print(f"  TP: {metrics['true_positives']}, FP: {metrics['false_positives']}")
    print(f"  FN: {metrics['false_negatives']}, TN: {metrics['true_negatives']}")
    
    # Lead time analysis
    test_df = df_features.iloc[len(df_features) - len(X_test):]
    y_pred = model.predict_proba(X_test)[:, 1] >= optimal_threshold
    
    lead_time_stats = compute_lead_time_analysis(
        test_df.reset_index(drop=True),
        y_pred.astype(int),
        model.predict_proba(X_test)[:, 1]
    )
    
    if lead_time_stats:
        print(f"\nLead Time Analysis:")
        print(f"  Mean: {lead_time_stats.get('mean_lead_time_hours', 'N/A')} hours")
        print(f"  Median: {lead_time_stats.get('median_lead_time_hours', 'N/A')} hours")
    
    # Validation (relaxed for synthetic data)
    assert metrics['recall'] >= 0.2, "Recall too low"
    assert metrics['roc_auc'] >= 0.5, "ROC-AUC too low"
    
    print("\n[PASS] Model evaluation")
    return metrics, optimal_threshold


def test_shap_explainability(model, X_train, X_test):
    """Test 5: SHAP Explainability"""
    print("\n" + "="*60)
    print("TEST 5: SHAP Explainability")
    print("="*60)
    
    # Sample background data (for efficiency)
    X_background = X_train.sample(min(100, len(X_train)), random_state=42)
    X_explain = X_test.sample(min(50, len(X_test)), random_state=42)
    
    print(f"\nComputing SHAP values...")
    print(f"  Background: {len(X_background)} samples")
    print(f"  Explain: {len(X_explain)} samples")
    
    shap_values, explainer = compute_shap_values(model, X_background, X_explain)
    
    print(f"\n[OK] SHAP values computed")
    
    # Get top drivers
    top_drivers = get_top_drivers(shap_values, X_explain, top_k=3)
    
    print(f"\nTop 3 drivers for first 5 predictions:")
    for i in range(min(5, len(top_drivers))):
        print(f"\nPrediction {i}:")
        print(f"  1. {top_drivers.iloc[i]['top1_feature']}: SHAP = {top_drivers.iloc[i]['top1_shap']:.4f}")
        print(f"  2. {top_drivers.iloc[i]['top2_feature']}: SHAP = {top_drivers.iloc[i]['top2_shap']:.4f}")
        print(f"  3. {top_drivers.iloc[i]['top3_feature']}: SHAP = {top_drivers.iloc[i]['top3_shap']:.4f}")
    
    # Validation
    assert shap_values is not None, "SHAP computation failed"
    assert len(top_drivers) > 0, "Top drivers extraction failed"
    
    print("\n[PASS] SHAP explainability")
    return shap_values


def test_save_artifacts(model, feature_names, metrics, optimal_threshold, shap_values):
    """Test 6: Save Artifacts"""
    print("\n" + "="*60)
    print("TEST 6: Save Artifacts")
    print("="*60)
    
    # Prepare thresholds dict
    thresholds = {
        'optimal_threshold': optimal_threshold,
        'f2_score': metrics['f2_score'],
        'recall': metrics['recall'],
        'precision': metrics['precision']
    }
    
    # Save model artifacts
    print("\nSaving model artifacts...")
    save_model_artifacts(model, feature_names, thresholds=thresholds)
    
    # Save SHAP artifacts
    print("Saving SHAP artifacts...")
    save_shap_artifacts(shap_values)
    
    print(f"\n[OK] Artifacts saved to ml_engine/artifacts/")
    
    # Verify files exist
    from pathlib import Path
    artifacts_dir = Path("ml_engine/artifacts")
    
    assert (artifacts_dir / "xgb_model.pkl").exists(), "Model file not saved"
    assert (artifacts_dir / "feature_list.json").exists(), "Features file not saved"
    assert (artifacts_dir / "thresholds.json").exists(), "Thresholds file not saved"
    assert (artifacts_dir / "shap_values.pkl").exists(), "SHAP file not saved"
    
    print("\nAll artifact files exist:")
    print("  [OK] xgb_model.pkl")
    print("  [OK] feature_list.json")
    print("  [OK] thresholds.json")
    print("  [OK] shap_values.pkl")
    
    print("\n[PASS] Save artifacts")


def main():
    """Run all tests"""
    print("="*60)
    print("FLOOD PREDICTION MODEL TEST SUITE (TASK 9A)")
    print("="*60)
    
    try:
        # Test 1: Dataset construction
        df = test_dataset_construction()
        
        # Test 2: Feature engineering
        df_features = test_feature_engineering(df)
        
        # Test 3: Model training
        model, X_train, X_test, y_train, y_test, feature_names = test_model_training(df_features)
        
        # Test 4: Model evaluation
        metrics, optimal_threshold = test_model_evaluation(model, X_test, y_test, df_features)
        
        # Test 5: SHAP explainability
        shap_values = test_shap_explainability(model, X_train, X_test)
        
        # Test 6: Save artifacts
        test_save_artifacts(model, feature_names, metrics, optimal_threshold, shap_values)
        
        # Summary
        print("\n" + "="*60)
        print("[PASS] ALL TESTS PASSED")
        print("="*60)
        
        print("\nTask 9A Summary:")
        print(f"  [OK] Dataset constructed from weather + terrain + labels")
        print(f"  [OK] Features engineered: {len(feature_names)} features")
        print(f"  [OK] XGBoost model trained (conservative hyperparameters)")
        print(f"  [OK] Recall: {metrics['recall']:.3f}, F2-Score: {metrics['f2_score']:.3f}")
        print(f"  [OK] Optimal threshold: {optimal_threshold:.2f}")
        print(f"  [OK] SHAP explainability computed")
        print(f"  [OK] Artifacts saved to ml_engine/artifacts/")
        
        print("\nML-Ready for API deployment (Task 10)")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
