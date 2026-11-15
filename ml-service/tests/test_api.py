"""
Unit tests for the FastAPI machine learning service endpoint logic and routing.
"""

import pytest
from app.main import (
    health_check, 
    predict_flare_probability, 
    get_metrics, 
    get_baseline_parameters, 
    get_model_metadata, 
    get_feature_importance
)
from app.schemas.forecast import PredictRequest

def test_health_check_function():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["service"] == "arkastra-ml-service"
    assert res["model_loaded"] is True
    assert res["available_model_version"] == "1.0.0"

def test_predict_function_elevated():
    req = PredictRequest(
        observation_timestamp="2024-05-10T12:00:00Z",
        current_long_flux=2.5e-5, # Elevated M-class level flux
        current_short_flux=5.0e-6,
        m_flares_prev_6h=1,
        m_flares_prev_24h=2,
        m_flares_prev_7d=5,
        x_flares_prev_24h=0,
        hours_since_last_m_flare=3.5,
        hours_since_last_x_flare=120.0
    )
    res = predict_flare_probability(req)
    assert res.success is True
    assert res.forecast_horizon_hours == 24
    assert 0.0 <= res.probability_m_plus <= 1.0
    assert res.probability_x_plus is None
    assert res.risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert 0.0 <= res.baseline_probability <= 1.0
    assert res.data_status == "FRESH"

def test_predict_function_quiet_sun():
    req = PredictRequest(
        observation_timestamp="2024-05-10T12:00:00Z",
        current_long_flux=1.2e-7, # Quiet Sun B-class flux
        m_flares_prev_24h=0
    )
    res = predict_flare_probability(req)
    assert res.success is True
    assert res.probability_m_plus < 0.50 # Quiet Sun should have low M-flare probability
    assert res.risk_level in ["LOW", "MODERATE"]

def test_metrics_function():
    data = get_metrics()
    assert "calibrated_model_metrics" in data
    assert "brier_score" in data["calibrated_model_metrics"]
    assert data["calibrated_model_metrics"]["brier_skill_score"] > 0.0

def test_baseline_function():
    data = get_baseline_parameters()
    assert "p_m_given_active" in data
    assert "p_m_given_quiet" in data
    assert data["p_m_given_active"] > data["p_m_given_quiet"]

def test_metadata_function():
    data = get_model_metadata()
    assert data["model_version"] == "1.0.0"
    assert data["forecast_horizon_hours"] == 24
    assert "training_sample_count" in data

def test_feature_importance_function():
    data = get_feature_importance()
    assert "top_features" in data
    assert len(data["top_features"]) > 0
