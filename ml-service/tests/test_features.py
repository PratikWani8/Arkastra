"""
Unit tests for solar time-series feature engineering.
"""

import pytest
import pandas as pd
import numpy as np
from training.feature_engineering import compute_solar_features, FEATURE_NAMES, SAFE_LOG_FLOOR

def test_feature_dimensions_and_finiteness():
    base_time = pd.to_datetime("2024-01-01T00:00:00Z")
    timestamps = [base_time + pd.Timedelta(hours=i) for i in range(50)]
    df_sample = pd.DataFrame({
        "timestamp": timestamps,
        "long_flux": np.linspace(1e-7, 1e-4, 50),
        "short_flux": np.linspace(2e-8, 2e-5, 50),
    })

    feats = compute_solar_features(df_sample)
    
    # Check that all features exist
    for f in FEATURE_NAMES:
        assert f in feats.columns, f"Missing feature: {f}"
        assert feats[f].isna().sum() == 0, f"Feature {f} contains NaNs"
        assert not np.isinf(feats[f]).any(), f"Feature {f} contains infinite values"

def test_safe_log_floor():
    base_time = pd.to_datetime("2024-01-01T00:00:00Z")
    df_sample = pd.DataFrame({
        "timestamp": [base_time],
        "long_flux": [0.0], # Zero or negative input must be floored safely
        "short_flux": [-1e-8]
    })
    feats = compute_solar_features(df_sample)
    assert feats["long_flux"].iloc[0] >= SAFE_LOG_FLOOR
    assert feats["short_flux"].iloc[0] >= SAFE_LOG_FLOOR * 0.1
    assert np.isfinite(feats["log_long_flux"].iloc[0])

def test_strictly_backward_flare_counts():
    base_time = pd.to_datetime("2024-01-01T12:00:00Z")
    df_sample = pd.DataFrame({
        "timestamp": [base_time],
        "long_flux": [1e-6],
        "short_flux": [2e-7]
    })
    
    # Flare in the future (+2h)
    future_flare = pd.DataFrame([{
        "begin_time": base_time + pd.Timedelta(hours=2),
        "is_m_plus": True,
        "is_x_plus": False
    }])
    feats_future = compute_solar_features(df_sample, future_flare)
    # The future flare must NOT be counted in previous flare features
    assert feats_future["m_flares_prev_6h"].iloc[0] == 0
    assert feats_future["m_flares_prev_24h"].iloc[0] == 0

    # Flare in the past (-2h)
    past_flare = pd.DataFrame([{
        "begin_time": base_time - pd.Timedelta(hours=2),
        "is_m_plus": True,
        "is_x_plus": False
    }])
    feats_past = compute_solar_features(df_sample, past_flare)
    assert feats_past["m_flares_prev_6h"].iloc[0] == 1
    assert feats_past["m_flares_prev_24h"].iloc[0] == 1
    assert feats_past["hours_since_last_m_flare"].iloc[0] == pytest.approx(2.0)
