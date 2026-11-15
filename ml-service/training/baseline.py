"""
ARKASTRA: Scientific Persistence Baseline
Implements the space weather persistence baseline:
"Tomorrow's solar activity state resembles today's recent activity state."
Estimates smoothed conditional probability:
P(M+ flare in next 24h | M+ flare in previous 24h)
Trained strictly on the training partition.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class PersistenceBaseline:
    def __init__(self, smoothing_alpha: float = 1.0):
        self.smoothing_alpha = smoothing_alpha
        self.p_m_given_active: float = 0.5
        self.p_m_given_quiet: float = 0.1
        self.climatological_prior: float = 0.2
        self.is_fitted: bool = False
        self.training_metadata: Dict[str, Any] = {}

    def fit(self, df_train: pd.DataFrame, recent_activity_col: str = "m_flares_prev_24h", target_col: str = "target_m_plus"):
        """
        Fits persistence baseline conditional probabilities using training data only.
        Applies Laplace smoothing: (count + alpha) / (total + 2*alpha)
        """
        # Active state: at least one M+ flare in previous 24 hours
        active_mask = (df_train[recent_activity_col] > 0)
        quiet_mask = ~active_mask

        n_active = int(active_mask.sum())
        n_quiet = int(quiet_mask.sum())

        pos_when_active = int(df_train.loc[active_mask, target_col].sum())
        pos_when_quiet = int(df_train.loc[quiet_mask, target_col].sum())

        # Smoothed conditional probabilities
        self.p_m_given_active = (pos_when_active + self.smoothing_alpha) / (n_active + 2.0 * self.smoothing_alpha)
        self.p_m_given_quiet = (pos_when_quiet + self.smoothing_alpha) / (n_quiet + 2.0 * self.smoothing_alpha)
        self.climatological_prior = (df_train[target_col].sum() + self.smoothing_alpha) / (len(df_train) + 2.0 * self.smoothing_alpha)

        self.is_fitted = True
        self.training_metadata = {
            "training_samples": len(df_train),
            "smoothing_alpha": self.smoothing_alpha,
            "n_active_state": n_active,
            "positives_when_active": pos_when_active,
            "p_m_given_active": float(self.p_m_given_active),
            "n_quiet_state": n_quiet,
            "positives_when_quiet": pos_when_quiet,
            "p_m_given_quiet": float(self.p_m_given_quiet),
            "climatological_prior": float(self.climatological_prior)
        }

        logger.info(f"Fitted Persistence Baseline: P(M+|Active) = {self.p_m_given_active:.4f}, P(M+|Quiet) = {self.p_m_given_quiet:.4f}")
        return self

    def predict_proba(self, df: pd.DataFrame, recent_activity_col: str = "m_flares_prev_24h") -> np.ndarray:
        """
        Returns an (N, 2) array of probabilities [P(no_flare), P(flare_in_24h)]
        conditioned strictly on whether recent activity occurred.
        """
        if not self.is_fitted:
            raise RuntimeError("PersistenceBaseline is not fitted yet.")

        active_mask = (df[recent_activity_col] > 0).values
        probs = np.where(active_mask, self.p_m_given_active, self.p_m_given_quiet)
        
        # Return 2D array [P(y=0), P(y=1)]
        return np.column_stack([1.0 - probs, probs])

    def save(self, filepath: str):
        data = {
            "model_type": "PersistenceBaseline",
            "p_m_given_active": self.p_m_given_active,
            "p_m_given_quiet": self.p_m_given_quiet,
            "climatological_prior": self.climatological_prior,
            "smoothing_alpha": self.smoothing_alpha,
            "training_metadata": self.training_metadata
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved persistence baseline parameters to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "PersistenceBaseline":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        baseline = cls(smoothing_alpha=data.get("smoothing_alpha", 1.0))
        baseline.p_m_given_active = data["p_m_given_active"]
        baseline.p_m_given_quiet = data["p_m_given_quiet"]
        baseline.climatological_prior = data.get("climatological_prior", 0.2)
        baseline.training_metadata = data.get("training_metadata", {})
        baseline.is_fitted = True
        return baseline
