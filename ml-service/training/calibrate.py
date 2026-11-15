"""
ARKASTRA: Scientific Probability Calibration
Applies Platt Scaling (Sigmoid) and Isotonic Regression to raw model scores.
Fitted strictly on validation data to prevent data leakage and produce reliable space weather probabilities.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss
import joblib

logger = logging.getLogger(__name__)

class ProbabilityCalibrator:
    def __init__(self, method: str = "sigmoid"):
        """
        method: 'sigmoid' (Platt scaling) or 'isotonic'
        """
        self.method = method
        self.calibrator = None
        self.is_fitted = False
        self.pre_calibration_brier: float = 0.0
        self.post_calibration_brier: float = 0.0

    def fit(self, raw_probs: np.ndarray, y_true: np.ndarray):
        """
        Fits calibration curve on validation predictions:
        maps raw uncalibrated probability p -> calibrated probability p_cal
        """
        raw_probs = np.clip(raw_probs, 1e-6, 1.0 - 1e-6)
        
        self.pre_calibration_brier = float(brier_score_loss(y_true, raw_probs))

        if self.method == "sigmoid":
            # Platt Scaling: Logistic regression on log-odds
            log_odds = np.log(raw_probs / (1.0 - raw_probs)).reshape(-1, 1)
            lr = LogisticRegression(C=1.0, solver="lbfgs")
            lr.fit(log_odds, y_true)
            self.calibrator = lr
            calibrated = lr.predict_proba(log_odds)[:, 1]
        elif self.method == "isotonic":
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            iso.fit(raw_probs, y_true)
            self.calibrator = iso
            calibrated = iso.predict(raw_probs)
        else:
            raise ValueError(f"Unknown calibration method: {self.method}")

        self.post_calibration_brier = float(brier_score_loss(y_true, calibrated))
        self.is_fitted = True
        logger.info(f"Calibration ({self.method}) fitted: Brier Score improved from {self.pre_calibration_brier:.4f} -> {self.post_calibration_brier:.4f}")
        return self

    def predict_proba(self, raw_probs: np.ndarray) -> np.ndarray:
        """
        Calibrates 1D array of positive class probabilities.
        Returns calibrated 1D probability array.
        """
        if not self.is_fitted:
            raise RuntimeError("Calibrator is not fitted.")

        raw_probs = np.clip(raw_probs, 1e-6, 1.0 - 1e-6)
        if self.method == "sigmoid":
            log_odds = np.log(raw_probs / (1.0 - raw_probs)).reshape(-1, 1)
            calibrated = self.calibrator.predict_proba(log_odds)[:, 1]
        else:
            calibrated = self.calibrator.predict(raw_probs)

        return np.clip(calibrated, 0.0, 1.0)

    def save(self, filepath: str):
        joblib.dump({
            "method": self.method,
            "calibrator": self.calibrator,
            "pre_calibration_brier": self.pre_calibration_brier,
            "post_calibration_brier": self.post_calibration_brier,
            "is_fitted": self.is_fitted
        }, filepath)
        logger.info(f"Saved calibrator artifact to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "ProbabilityCalibrator":
        data = joblib.load(filepath)
        obj = cls(method=data["method"])
        obj.calibrator = data["calibrator"]
        obj.pre_calibration_brier = data["pre_calibration_brier"]
        obj.post_calibration_brier = data["post_calibration_brier"]
        obj.is_fitted = data["is_fitted"]
        return obj
