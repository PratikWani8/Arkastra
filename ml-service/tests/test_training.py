"""
Unit tests for trained model loading, inference, calibration, and persistence baseline.
"""

import os
import pytest
import numpy as np
import joblib
from training.baseline import PersistenceBaseline
from training.calibrate import ProbabilityCalibrator

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(BASE_DIR, "models")

def test_model_artifacts_exist():
    assert os.path.exists(os.path.join(MODELS_DIR, "arkastra_mplus_model.joblib"))
    assert os.path.exists(os.path.join(MODELS_DIR, "arkastra_preprocessor.joblib"))
    assert os.path.exists(os.path.join(MODELS_DIR, "arkastra_calibrator.joblib"))
    assert os.path.exists(os.path.join(MODELS_DIR, "arkastra_persistence_baseline.json"))
    assert os.path.exists(os.path.join(MODELS_DIR, "arkastra_model_metadata.json"))

def test_calibrator_inference():
    calibrator_path = os.path.join(MODELS_DIR, "arkastra_calibrator.joblib")
    calibrator = ProbabilityCalibrator.load(calibrator_path)
    
    raw_probs = np.array([0.05, 0.25, 0.50, 0.75, 0.95])
    cal_probs = calibrator.predict_proba(raw_probs)
    
    assert len(cal_probs) == 5
    assert np.all(cal_probs >= 0.0)
    assert np.all(cal_probs <= 1.0)
    # Monotonicity check: higher raw probability should yield higher calibrated probability
    assert cal_probs[0] <= cal_probs[-1]

def test_baseline_inference():
    baseline_path = os.path.join(MODELS_DIR, "arkastra_persistence_baseline.json")
    baseline = PersistenceBaseline.load(baseline_path)
    
    import pandas as pd
    sample_df = pd.DataFrame({"m_flares_prev_24h": [0, 1, 0, 3]})
    probs = baseline.predict_proba(sample_df)
    
    assert probs.shape == (4, 2)
    assert np.allclose(probs.sum(axis=1), 1.0)
    # When recent activity is 0 (quiet), probability must equal p_m_given_quiet
    assert probs[0, 1] == pytest.approx(baseline.p_m_given_quiet)
    # When recent activity is >0 (active), probability must equal p_m_given_active
    assert probs[1, 1] == pytest.approx(baseline.p_m_given_active)
