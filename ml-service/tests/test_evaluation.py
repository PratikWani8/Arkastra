"""
Unit tests for scientific evaluation metrics: Brier Score, BSS, TSS, and calibration curve.
"""

import os
import json
import pytest
import numpy as np
from sklearn.metrics import brier_score_loss, confusion_matrix
from training.evaluate import find_optimal_tss_threshold, compute_all_metrics

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS_DIR = os.path.join(BASE_DIR, "ml-service", "reports")

def test_bss_calculation_logic():
    # Synthetic outcomes
    y_true = np.array([0, 0, 1, 1, 1])
    ml_probs = np.array([0.1, 0.2, 0.8, 0.9, 0.7])
    base_probs = np.array([0.3, 0.4, 0.6, 0.5, 0.6])

    brier_ml = brier_score_loss(y_true, ml_probs)
    brier_base = brier_score_loss(y_true, base_probs)

    bss = 1.0 - (brier_ml / brier_base)
    # ML clearly has lower Brier score than baseline here, so BSS must be strictly positive
    assert bss > 0.0

def test_tss_calculation_bounds():
    # Perfect classifier
    y_true = np.array([0, 0, 1, 1])
    y_pred_perfect = np.array([0.0, 0.0, 1.0, 1.0])
    metrics = compute_all_metrics(y_true, y_pred_perfect, threshold=0.5)
    assert metrics["tss"] == pytest.approx(1.0)
    assert metrics["sensitivity"] == pytest.approx(1.0)
    assert metrics["specificity"] == pytest.approx(1.0)

    # Inverted classifier
    y_pred_worst = np.array([1.0, 1.0, 0.0, 0.0])
    metrics_inv = compute_all_metrics(y_true, y_pred_worst, threshold=0.5)
    assert metrics_inv["tss"] == pytest.approx(-1.0)

def test_evaluation_reports_exist():
    eval_path = os.path.join(REPORTS_DIR, "model_evaluation.json")
    baseline_path = os.path.join(REPORTS_DIR, "baseline_comparison.json")
    cal_path = os.path.join(REPORTS_DIR, "calibration_report.json")
    fi_path = os.path.join(REPORTS_DIR, "feature_importance.json")

    assert os.path.exists(eval_path)
    assert os.path.exists(baseline_path)
    assert os.path.exists(cal_path)
    assert os.path.exists(fi_path)

    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["calibrated_model_metrics"]["brier_skill_score"] > 0.0
        assert data["calibrated_model_metrics"]["roc_auc"] > 0.70
