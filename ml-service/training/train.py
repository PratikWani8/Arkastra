"""
ARKASTRA: Machine Learning Model Training & Baseline Pipeline
Trains candidate classification algorithms:
1. Logistic Regression (L2 regularized)
2. Random Forest Classifier
3. XGBoost Classifier (with class imbalance weighting)
Performs probability calibration (Platt scaling), persistence baseline fitting,
and saves production model artifacts to models/.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
import joblib

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score, average_precision_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from training.feature_engineering import FEATURE_NAMES
from training.baseline import PersistenceBaseline
from training.calibrate import ProbabilityCalibrator

logger = logging.getLogger("ArkastraTrainer")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "datasets", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "ml-service", "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

def train_pipeline():
    logger.info("==================================================")
    logger.info("ARKASTRA MODEL TRAINING PIPELINE INITIATED")
    logger.info("==================================================")

    # 1. Load Processed Dataset
    features_path = os.path.join(PROCESSED_DIR, "features.parquet")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found at {features_path}. Run Phase 4 first.")

    df = pd.read_parquet(features_path)
    logger.info(f"Loaded dataset: {df.shape[0]} samples with {len(FEATURE_NAMES)} features.")

    # 2. Extract Chronological Partitions
    train_df = df[df["split"] == "train"].copy()
    val_df = df[df["split"] == "val"].copy()
    test_df = df[df["split"] == "test"].copy()

    X_train = train_df[FEATURE_NAMES].values
    y_train = train_df["target_m_plus"].values

    X_val = val_df[FEATURE_NAMES].values
    y_val = val_df["target_m_plus"].values

    X_test = test_df[FEATURE_NAMES].values
    y_test = test_df["target_m_plus"].values

    logger.info(f"Train samples: {len(X_train)} (Positives: {y_train.sum()} / {y_train.mean()*100:.1f}%)")
    logger.info(f"Validation samples: {len(X_val)} (Positives: {y_val.sum()} / {y_val.mean()*100:.1f}%)")
    logger.info(f"Test samples (Untouched): {len(X_test)} (Positives: {y_test.sum()} / {y_test.mean()*100:.1f}%)")

    # 3. Fit Preprocessor (StandardScaler) on TRAINING DATA ONLY
    preprocessor = StandardScaler()
    X_train_scaled = preprocessor.fit_transform(X_train)
    X_val_scaled = preprocessor.transform(X_val)
    # Save preprocessor artifact
    preprocessor_path = os.path.join(MODELS_DIR, "arkastra_preprocessor.joblib")
    joblib.dump(preprocessor, preprocessor_path)
    logger.info(f"Fitted and saved preprocessor to {preprocessor_path}")

    # 4. Fit Scientific Persistence Baseline on TRAINING DATA ONLY
    baseline = PersistenceBaseline(smoothing_alpha=1.0)
    baseline.fit(train_df, recent_activity_col="m_flares_prev_24h", target_col="target_m_plus")
    baseline_path = os.path.join(MODELS_DIR, "arkastra_persistence_baseline.json")
    baseline.save(baseline_path)

    # Baseline validation performance
    base_val_probs = baseline.predict_proba(val_df)[:, 1]
    base_val_brier = brier_score_loss(y_val, base_val_probs)
    base_val_auc = roc_auc_score(y_val, base_val_probs)
    logger.info(f"Persistence Baseline Validation -> Brier: {base_val_brier:.4f}, ROC-AUC: {base_val_auc:.4f}")

    # 5. Train Candidate ML Models
    # Calculate scale_pos_weight for imbalance handling: negative / positive
    pos_count = max(1, int(y_train.sum()))
    neg_count = max(1, len(y_train) - pos_count)
    scale_pos_weight = neg_count / pos_count

    candidates: Dict[str, Any] = {
        "LogisticRegression": LogisticRegression(
            C=0.1, 
            class_weight="balanced", 
            max_iter=1000, 
            random_state=42
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=150, 
            max_depth=8, 
            class_weight="balanced", 
            random_state=42, 
            n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            scale_pos_weight=scale_pos_weight,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        )
    }

    best_model_name = None
    best_model = None
    best_val_brier = float("inf")
    candidate_val_results = {}

    for name, model in candidates.items():
        logger.info(f"Training candidate model: {name}...")
        if name == "LogisticRegression":
            model.fit(X_train_scaled, y_train)
            val_probs = model.predict_proba(X_val_scaled)[:, 1]
        else:
            # Tree models fit directly on feature matrix
            model.fit(X_train, y_train)
            val_probs = model.predict_proba(X_val)[:, 1]

        val_brier = brier_score_loss(y_val, val_probs)
        val_auc = roc_auc_score(y_val, val_probs)
        val_prauc = average_precision_score(y_val, val_probs)

        candidate_val_results[name] = {
            "val_brier_score": float(val_brier),
            "val_roc_auc": float(val_auc),
            "val_pr_auc": float(val_prauc)
        }
        logger.info(f"  {name} Val -> Brier: {val_brier:.4f}, ROC-AUC: {val_auc:.4f}, PR-AUC: {val_prauc:.4f}")

        if val_brier < best_val_brier:
            best_val_brier = val_brier
            best_model_name = name
            best_model = model

    logger.info(f"Selected Candidate: {best_model_name} (Validation Brier: {best_val_brier:.4f})")

    # 6. Fit Probability Calibrator on Validation Data
    logger.info("Fitting Probability Calibrator on Validation Predictions...")
    if best_model_name == "LogisticRegression":
        val_raw_probs = best_model.predict_proba(X_val_scaled)[:, 1]
    else:
        val_raw_probs = best_model.predict_proba(X_val)[:, 1]

    calibrator = ProbabilityCalibrator(method="sigmoid")
    calibrator.fit(val_raw_probs, y_val)
    calibrator_path = os.path.join(MODELS_DIR, "arkastra_calibrator.joblib")
    calibrator.save(calibrator_path)

    # 7. Model Explainability & Feature Importance
    feature_importances = []
    if hasattr(best_model, "feature_importances_"):
        raw_importances = best_model.feature_importances_
        for feat, imp in sorted(zip(FEATURE_NAMES, raw_importances), key=lambda x: x[1], reverse=True):
            feature_importances.append({"feature": feat, "importance": float(imp)})
    elif hasattr(best_model, "coef_"):
        coefs = np.abs(best_model.coef_[0])
        for feat, imp in sorted(zip(FEATURE_NAMES, coefs), key=lambda x: x[1], reverse=True):
            feature_importances.append({"feature": feat, "importance": float(imp)})

    explainability_report = {
        "model_name": f"Arkastra {best_model_name}",
        "feature_count": len(FEATURE_NAMES),
        "top_features": feature_importances[:15],
        "all_features": feature_importances
    }
    fi_path = os.path.join(REPORTS_DIR, "feature_importance.json")
    with open(fi_path, "w", encoding="utf-8") as f:
        json.dump(explainability_report, f, indent=2)
    logger.info(f"Saved feature importance report to {fi_path}")

    # 8. Save Selected Model Artifact
    model_path = os.path.join(MODELS_DIR, "arkastra_mplus_model.joblib")
    joblib.dump(best_model, model_path)
    logger.info(f"Saved selected model artifact to {model_path}")

    # 9. Save Feature Schema & Production Metadata
    schema_info = {
        "model_name": f"Arkastra {best_model_name}",
        "model_version": "1.0.0",
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "requires_scaling": (best_model_name == "LogisticRegression")
    }
    schema_path = os.path.join(MODELS_DIR, "arkastra_feature_schema.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema_info, f, indent=2)

    metadata = {
        "model_name": f"Arkastra {best_model_name}",
        "algorithm": best_model_name,
        "model_version": "1.0.0",
        "trained_at_utc": datetime.utcnow().isoformat() + "Z",
        "forecast_horizon_hours": 24,
        "training_sample_count": len(X_train),
        "validation_sample_count": len(X_val),
        "test_sample_count": len(X_test),
        "train_positives": int(y_train.sum()),
        "train_negatives": int(len(y_train) - y_train.sum()),
        "validation_brier_score": float(best_val_brier),
        "calibration_method": "Platt Scaling (Sigmoid)",
        "candidate_comparison": candidate_val_results,
        "artifacts": {
            "model": "arkastra_mplus_model.joblib",
            "preprocessor": "arkastra_preprocessor.joblib",
            "calibrator": "arkastra_calibrator.joblib",
            "baseline": "arkastra_persistence_baseline.json",
            "schema": "arkastra_feature_schema.json"
        }
    }
    metadata_path = os.path.join(MODELS_DIR, "arkastra_model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved production model metadata to {metadata_path}")

    logger.info("==================================================")
    logger.info("PHASE 5 TRAINING & BASELINE COMPLETED SUCCESSFULLY")
    logger.info("==================================================")
    return best_model, metadata

if __name__ == "__main__":
    train_pipeline()
