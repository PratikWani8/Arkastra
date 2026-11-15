"""
ARKASTRA: Scientific Model Evaluation & Persistence Baseline Comparison
Evaluates calibrated ML model and Persistence Baseline on the untouched chronological test partition:
- Brier Score & Brier Skill Score (BSS)
- True Skill Statistic (TSS = Sensitivity + Specificity - 1)
- Validation-derived optimal threshold selection
- ROC-AUC, PR-AUC, Precision, Recall, F1, False Alarm Rate (FAR)
- 8 Scientific Evaluation Figures and JSON reports
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

# Ensure matplotlib writable temp cache
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(__file__), "..", ".mpl_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import (
    brier_score_loss, roc_auc_score, average_precision_score,
    roc_curve, precision_recall_curve, confusion_matrix,
    precision_score, recall_score, f1_score
)
from sklearn.calibration import calibration_curve

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from training.feature_engineering import FEATURE_NAMES
from training.baseline import PersistenceBaseline
from training.calibrate import ProbabilityCalibrator

logger = logging.getLogger("ArkastraEvaluator")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "datasets", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "ml-service", "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

def find_optimal_tss_threshold(y_true: np.ndarray, y_probs: np.ndarray) -> Tuple[float, float]:
    """
    Finds the probability threshold that maximizes True Skill Statistic (TSS)
    using VALIDATION data only.
    TSS = Sensitivity + Specificity - 1
    """
    thresholds = np.linspace(0.05, 0.95, 91)
    best_threshold = 0.5
    best_tss = -1.0

    for thresh in thresholds:
        preds = (y_probs >= thresh).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()
        
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        tss = sensitivity + specificity - 1.0

        if tss > best_tss:
            best_tss = tss
            best_threshold = thresh

    return float(best_threshold), float(best_tss)

def compute_all_metrics(y_true: np.ndarray, y_probs: np.ndarray, threshold: float) -> Dict[str, Any]:
    preds = (y_probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    tss = sensitivity + specificity - 1.0
    far = fp / (fp + tn) if (fp + tn) > 0 else 0.0 # False alarm rate

    brier = float(brier_score_loss(y_true, y_probs))
    roc_auc = float(roc_auc_score(y_true, y_probs))
    pr_auc = float(average_precision_score(y_true, y_probs))
    precision = float(precision_score(y_true, preds, zero_division=0))
    recall = float(recall_score(y_true, preds, zero_division=0))
    f1 = float(f1_score(y_true, preds, zero_division=0))

    return {
        "brier_score": brier,
        "tss": float(tss),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "false_alarm_rate": float(far),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "operating_threshold": float(threshold)
    }

def run_evaluation():
    logger.info("==================================================")
    logger.info("ARKASTRA SCIENTIFIC MODEL EVALUATION")
    logger.info("==================================================")

    # 1. Load Data
    features_path = os.path.join(PROCESSED_DIR, "features.parquet")
    df = pd.read_parquet(features_path)

    val_df = df[df["split"] == "val"].copy()
    test_df = df[df["split"] == "test"].copy()

    X_val = val_df[FEATURE_NAMES].values
    y_val = val_df["target_m_plus"].values

    X_test = test_df[FEATURE_NAMES].values
    y_test = test_df["target_m_plus"].values

    logger.info(f"Test Partition (Untouched): {len(y_test)} samples (Positives: {y_test.sum()})")

    # 2. Load Artifacts
    model = joblib.load(os.path.join(MODELS_DIR, "arkastra_mplus_model.joblib"))
    preprocessor = joblib.load(os.path.join(MODELS_DIR, "arkastra_preprocessor.joblib"))
    calibrator = ProbabilityCalibrator.load(os.path.join(MODELS_DIR, "arkastra_calibrator.joblib"))
    baseline = PersistenceBaseline.load(os.path.join(MODELS_DIR, "arkastra_persistence_baseline.json"))

    # Determine if model requires scaling
    requires_scaling = hasattr(model, "coef_")
    X_val_eval = preprocessor.transform(X_val) if requires_scaling else X_val
    X_test_eval = preprocessor.transform(X_test) if requires_scaling else X_test

    # 3. Model Predictions on Validation Data (for threshold tuning ONLY)
    val_raw_probs = model.predict_proba(X_val_eval)[:, 1]
    val_cal_probs = calibrator.predict_proba(val_raw_probs)
    
    # Optimize TSS threshold on validation calibrated probabilities ONLY
    opt_threshold, val_tss = find_optimal_tss_threshold(y_val, val_cal_probs)
    logger.info(f"Optimal TSS Threshold tuned on VALIDATION data: {opt_threshold:.2f} (Val TSS: {val_tss:.4f})")

    # 4. Final Inference on Untouched Chronological Test Set
    test_raw_probs = model.predict_proba(X_test_eval)[:, 1]
    test_cal_probs = calibrator.predict_proba(test_raw_probs)
    test_base_probs = baseline.predict_proba(test_df)[:, 1]

    # 5. Compute Comprehensive Metrics on Test Set
    metrics_cal = compute_all_metrics(y_test, test_cal_probs, opt_threshold)
    metrics_raw = compute_all_metrics(y_test, test_raw_probs, opt_threshold)
    metrics_base = compute_all_metrics(y_test, test_base_probs, opt_threshold)

    # 6. Brier Skill Score (BSS) relative to Persistence Baseline
    # BSS = 1 - (Brier_ML / Brier_Baseline)
    base_brier = metrics_base["brier_score"]
    ml_brier = metrics_cal["brier_score"]
    bss = (1.0 - (ml_brier / base_brier)) if base_brier > 0 else 0.0

    metrics_cal["brier_skill_score"] = float(bss)

    logger.info("--------------------------------------------------")
    logger.info("FINAL UNTOUCHED TEST SET SCIENTIFIC RESULTS:")
    logger.info(f"  Calibrated ML Brier Score: {metrics_cal['brier_score']:.4f}")
    logger.info(f"  Persistence Baseline Brier: {metrics_base['brier_score']:.4f}")
    logger.info(f"  Brier Skill Score (BSS):   {bss:+.4f} ({'Skill gain over baseline' if bss > 0 else 'Baseline equivalent/ahead'})")
    logger.info(f"  True Skill Statistic (TSS):{metrics_cal['tss']:.4f} (Sensitivity: {metrics_cal['sensitivity']:.4f}, Specificity: {metrics_cal['specificity']:.4f})")
    logger.info(f"  ROC-AUC:                   {metrics_cal['roc_auc']:.4f}")
    logger.info(f"  PR-AUC:                    {metrics_cal['pr_auc']:.4f}")
    logger.info("--------------------------------------------------")

    # 7. Comparison Table Manifest
    comparison_table = [
        {"metric": "Brier Score", "arkastra_ml": metrics_cal["brier_score"], "persistence_baseline": metrics_base["brier_score"], "better": "lower"},
        {"metric": "Brier Skill Score (BSS)", "arkastra_ml": float(bss), "persistence_baseline": 0.0, "better": "higher"},
        {"metric": "True Skill Statistic (TSS)", "arkastra_ml": metrics_cal["tss"], "persistence_baseline": metrics_base["tss"], "better": "higher"},
        {"metric": "ROC-AUC", "arkastra_ml": metrics_cal["roc_auc"], "persistence_baseline": metrics_base["roc_auc"], "better": "higher"},
        {"metric": "PR-AUC", "arkastra_ml": metrics_cal["pr_auc"], "persistence_baseline": metrics_base["pr_auc"], "better": "higher"},
        {"metric": "Precision", "arkastra_ml": metrics_cal["precision"], "persistence_baseline": metrics_base["precision"], "better": "higher"},
        {"metric": "Recall / Sensitivity", "arkastra_ml": metrics_cal["recall"], "persistence_baseline": metrics_base["recall"], "better": "higher"},
        {"metric": "Specificity", "arkastra_ml": metrics_cal["specificity"], "persistence_baseline": metrics_base["specificity"], "better": "higher"},
        {"metric": "F1 Score", "arkastra_ml": metrics_cal["f1_score"], "persistence_baseline": metrics_base["f1_score"], "better": "higher"}
    ]

    # Save JSON reports
    eval_report = {
        "evaluation_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "dataset_partition": "test",
        "sample_count": len(y_test),
        "positive_event_count": int(y_test.sum()),
        "negative_event_count": int(len(y_test) - y_test.sum()),
        "test_period": {
            "start": test_df["timestamp"].min().isoformat(),
            "end": test_df["timestamp"].max().isoformat()
        },
        "calibrated_model_metrics": metrics_cal,
        "uncalibrated_model_metrics": metrics_raw,
        "persistence_baseline_metrics": metrics_base
    }

    with open(os.path.join(REPORTS_DIR, "model_evaluation.json"), "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    with open(os.path.join(REPORTS_DIR, "baseline_comparison.json"), "w", encoding="utf-8") as f:
        json.dump({
            "generated_at_utc": datetime.utcnow().isoformat() + "Z",
            "bss": float(bss),
            "comparison": comparison_table
        }, f, indent=2)

    # 8. Calibration Analysis Report
    prob_true, prob_pred = calibration_curve(y_test, test_cal_probs, n_bins=10, strategy="uniform")
    cal_report = {
        "method": "Platt Scaling (Sigmoid)",
        "pre_cal_brier": metrics_raw["brier_score"],
        "post_cal_brier": metrics_cal["brier_score"],
        "calibration_bins": [
            {"predicted_mean": float(p_p), "observed_frequency": float(p_t)}
            for p_p, p_t in zip(prob_pred, prob_true)
        ]
    }
    with open(os.path.join(REPORTS_DIR, "calibration_report.json"), "w", encoding="utf-8") as f:
        json.dump(cal_report, f, indent=2)

    # 9. Generate 8 Scientific Figures
    generate_eval_figures(
        y_test=y_test,
        cal_probs=test_cal_probs,
        raw_probs=test_raw_probs,
        base_probs=test_base_probs,
        metrics_cal=metrics_cal,
        metrics_raw=metrics_raw,
        metrics_base=metrics_base,
        bss=bss,
        figures_dir=FIGURES_DIR
    )

    logger.info("==================================================")
    logger.info("PHASE 6 SCIENTIFIC EVALUATION COMPLETED")
    logger.info("==================================================")
    return eval_report

def generate_eval_figures(
    y_test: np.ndarray,
    cal_probs: np.ndarray,
    raw_probs: np.ndarray,
    base_probs: np.ndarray,
    metrics_cal: Dict[str, Any],
    metrics_raw: Dict[str, Any],
    metrics_base: Dict[str, Any],
    bss: float,
    figures_dir: str
):
    logger.info("Generating 8 Scientific Evaluation Figures...")

    # 1. Reliability Diagram
    fig, ax = plt.subplots(figsize=(7, 6))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    p_true, p_pred = calibration_curve(y_test, cal_probs, n_bins=10)
    ax.plot([0, 1], [0, 1], "w--", alpha=0.5, label="Perfect Reliability (y = x)")
    ax.plot(p_pred, p_true, "s-", color='#f59e0b', lw=2, label=f"Calibrated ML (Brier={metrics_cal['brier_score']:.4f})")
    ax.set_title("Figure 1: Reliability Diagram (Untouched Test Period)", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_xlabel("Mean Predicted Probability", color='#94a3b8')
    ax.set_ylabel("Observed Flare Frequency", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, color='#1e293b', alpha=0.5)
    ax.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0')
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_reliability_diagram.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 2. ROC Curve
    fig, ax = plt.subplots(figsize=(7, 6))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    fpr_m, tpr_m, _ = roc_curve(y_test, cal_probs)
    fpr_b, tpr_b, _ = roc_curve(y_test, base_probs)
    ax.plot(fpr_m, tpr_m, color='#f59e0b', lw=2.5, label=f"Arkastra ML (ROC-AUC={metrics_cal['roc_auc']:.3f})")
    ax.plot(fpr_b, tpr_b, color='#38bdf8', lw=1.8, ls='--', label=f"Persistence Baseline (ROC-AUC={metrics_base['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], 'w:', alpha=0.4, label="No Skill (0.500)")
    ax.set_title("Figure 2: Receiver Operating Characteristic (ROC)", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_xlabel("False Positive Rate (1 - Specificity)", color='#94a3b8')
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, color='#1e293b', alpha=0.5)
    ax.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_roc_curve.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 3. Precision-Recall Curve
    fig, ax = plt.subplots(figsize=(7, 6))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    p_m, r_m, _ = precision_recall_curve(y_test, cal_probs)
    p_b, r_b, _ = precision_recall_curve(y_test, base_probs)
    ax.plot(r_m, p_m, color='#f59e0b', lw=2.5, label=f"Arkastra ML (PR-AUC={metrics_cal['pr_auc']:.3f})")
    ax.plot(r_b, p_b, color='#38bdf8', lw=1.8, ls='--', label=f"Persistence Baseline (PR-AUC={metrics_base['pr_auc']:.3f})")
    ax.set_title("Figure 3: Precision-Recall Curve (PR-AUC)", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_xlabel("Recall (Sensitivity)", color='#94a3b8')
    ax.set_ylabel("Precision", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, color='#1e293b', alpha=0.5)
    ax.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', loc='lower left')
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_pr_curve.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 4. Confusion Matrix Heatmap
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    cm = [
        [metrics_cal["confusion_matrix"]["true_negatives"], metrics_cal["confusion_matrix"]["false_positives"]],
        [metrics_cal["confusion_matrix"]["false_negatives"], metrics_cal["confusion_matrix"]["true_positives"]]
    ]
    cax = ax.matshow(cm, cmap='YlOrRd')
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i][j]}", ha='center', va='center', color='black' if cm[i][j] > 400 else 'white', fontweight='bold', fontsize=14)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Pred: 0', 'Pred: 1'], color='#94a3b8')
    ax.set_yticklabels(['Actual: 0', 'Actual: 1'], color='#94a3b8')
    ax.set_title("Figure 4: Confusion Matrix (Test Partition)", color='#f8fafc', fontsize=12, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_confusion_matrix.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 5. Brier Score & BSS Comparison
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    bars = ax.bar(["Arkastra ML", "Persistence Baseline"], [metrics_cal["brier_score"], metrics_base["brier_score"]], color=['#f59e0b', '#38bdf8'], width=0.4, edgecolor='#000000')
    for b in bars:
        h = b.get_height()
        ax.annotate(f"{h:.4f}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha='center', color='#f8fafc', fontweight='bold')
    ax.set_title(f"Figure 5: Brier Score Comparison (BSS = {bss:+.4f})", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Brier Score (Lower is Better)", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, axis='y', color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_brier_comparison.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 6. Uncalibrated vs Calibrated Comparison
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    bars = ax.bar(["Uncalibrated ML", "Calibrated ML"], [metrics_raw["brier_score"], metrics_cal["brier_score"]], color=['#ef4444', '#10b981'], width=0.4, edgecolor='#000000')
    for b in bars:
        h = b.get_height()
        ax.annotate(f"{h:.4f}", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha='center', color='#f8fafc', fontweight='bold')
    ax.set_title("Figure 6: Probability Calibration Impact on Brier Score", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Brier Score", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, axis='y', color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_calibration_comparison.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 7. Top Feature Importance
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    fi_path = os.path.join(REPORTS_DIR, "feature_importance.json")
    if os.path.exists(fi_path):
        with open(fi_path, "r", encoding="utf-8") as f:
            fi_data = json.load(f)
        top_feats = fi_data.get("top_features", [])[:10]
        f_names = [x["feature"] for x in top_feats][::-1]
        f_imps = [x["importance"] for x in top_feats][::-1]
        ax.barh(f_names, f_imps, color='#f59e0b', edgecolor='#000000')
    ax.set_title("Figure 7: Top Predictive Solar Activity Features", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_xlabel("Relative Importance / Absolute Weight", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, axis='x', color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_feature_importance.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 8. Predicted Probability Distribution
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    ax.hist(cal_probs[y_test == 0], bins=30, alpha=0.6, color='#38bdf8', label="Quiet Sun (y=0)", density=True)
    ax.hist(cal_probs[y_test == 1], bins=30, alpha=0.6, color='#ef4444', label="Actual M+ Flare Occurred (y=1)", density=True)
    ax.set_title("Figure 8: Forecasted Probability Distribution by Actual Outcome", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_xlabel("Predicted 24h M+ Flare Probability", color='#94a3b8')
    ax.set_ylabel("Probability Density", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, color='#1e293b', alpha=0.4)
    ax.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0')
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eval_probability_distribution.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    logger.info("All 8 scientific evaluation figures saved successfully.")

if __name__ == "__main__":
    run_evaluation()
