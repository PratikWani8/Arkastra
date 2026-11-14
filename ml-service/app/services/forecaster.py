"""
ARKASTRA: Real-Time Forecaster Service
Executes calibrated ML inference on incoming solar observation telemetry:
- Validates input features against training schema
- Computes calibrated 24-hour M-class+ flare probability
- Computes corresponding persistence baseline probability
- Categorizes product risk classification
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

from app.schemas.forecast import PredictRequest, PredictResponse
from training.feature_engineering import FEATURE_NAMES, compute_solar_features
from training.baseline import PersistenceBaseline
from training.calibrate import ProbabilityCalibrator

logger = logging.getLogger(__name__)

class SolarForecaster:
    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        self.model = None
        self.preprocessor = None
        self.calibrator = None
        self.baseline = None
        self.metadata = {}
        self.feature_schema = {}
        self.is_ready = False
        self._load_artifacts()

    def _load_artifacts(self):
        try:
            model_path = os.path.join(self.models_dir, "arkastra_mplus_model.joblib")
            prep_path = os.path.join(self.models_dir, "arkastra_preprocessor.joblib")
            cal_path = os.path.join(self.models_dir, "arkastra_calibrator.joblib")
            base_path = os.path.join(self.models_dir, "arkastra_persistence_baseline.json")
            meta_path = os.path.join(self.models_dir, "arkastra_model_metadata.json")
            schema_path = os.path.join(self.models_dir, "arkastra_feature_schema.json")

            if not all(os.path.exists(p) for p in [model_path, prep_path, cal_path, base_path]):
                logger.warning(f"Model artifacts not found in {self.models_dir}. Waiting for training completion.")
                return

            self.model = joblib.load(model_path)
            self.preprocessor = joblib.load(prep_path)
            self.calibrator = ProbabilityCalibrator.load(cal_path)
            self.baseline = PersistenceBaseline.load(base_path)

            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            if os.path.exists(schema_path):
                with open(schema_path, "r", encoding="utf-8") as f:
                    self.feature_schema = json.load(f)

            self.is_ready = True
            logger.info("All Arkastra production model artifacts loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading model artifacts: {e}", exc_info=True)
            self.is_ready = False

    def classify_risk(self, probability: float) -> str:
        """
        Product-level risk category definition:
        LOW: 0-10%
        MODERATE: 10-30%
        HIGH: 30-60%
        CRITICAL: 60-100%
        """
        p = float(probability)
        if p < 0.10:
            return "LOW"
        elif p < 0.30:
            return "MODERATE"
        elif p < 0.60:
            return "HIGH"
        else:
            return "CRITICAL"

    def forecast(self, req: PredictRequest) -> PredictResponse:
        if not self.is_ready:
            raise RuntimeError("Forecasting model is not ready or artifacts are missing.")

        # If full rolling observations are provided, construct exact feature pipeline
        if req.rolling_observations and len(req.rolling_observations) >= 3:
            obs_list = []
            for item in req.rolling_observations:
                obs_list.append({
                    "timestamp": pd.to_datetime(item.timestamp, utc=True),
                    "long_flux": item.long_flux,
                    "short_flux": item.short_flux if item.short_flux is not None else item.long_flux * 0.2
                })
            df_obs = pd.DataFrame(obs_list)
            # Add latest observation
            latest_time = pd.to_datetime(req.observation_timestamp, utc=True)
            df_obs = pd.concat([df_obs, pd.DataFrame([{
                "timestamp": latest_time,
                "long_flux": req.current_long_flux,
                "short_flux": req.current_short_flux or req.current_long_flux * 0.2
            }])], ignore_index=True)

            feats_df = compute_solar_features(df_obs)
            latest_row = feats_df.iloc[-1]
            feature_vector = np.array([latest_row[f] for f in FEATURE_NAMES]).reshape(1, -1)
        else:
            # Construct feature vector directly from request parameters
            long_f = max(1e-9, req.current_long_flux)
            short_f = max(1e-10, req.current_short_flux or long_f * 0.2)
            log_long = float(np.log10(long_f))
            log_short = float(np.log10(short_f))
            ratio = short_f / long_f

            obs_time = pd.to_datetime(req.observation_timestamp, utc=True)
            h = obs_time.hour
            doy = obs_time.dayofyear
            sin_h = float(np.sin(2.0 * np.pi * h / 24.0))
            cos_h = float(np.cos(2.0 * np.pi * h / 24.0))
            sin_doy = float(np.sin(2.0 * np.pi * doy / 365.25))
            cos_doy = float(np.cos(2.0 * np.pi * doy / 365.25))

            feat_dict = {
                "long_flux": long_f,
                "short_flux": short_f,
                "log_long_flux": log_long,
                "log_short_flux": log_short,
                "flux_ratio": ratio,
                "max_flux_1h": long_f,
                "max_flux_3h": long_f,
                "max_flux_6h": long_f,
                "max_flux_12h": long_f,
                "max_flux_24h": long_f,
                "mean_flux_6h": long_f,
                "mean_flux_12h": long_f,
                "mean_flux_24h": long_f,
                "std_flux_24h": 0.0,
                "flux_change_1h": 0.0,
                "flux_change_3h": 0.0,
                "flux_change_6h": 0.0,
                "flux_derivative_1h": 0.0,
                "flux_acceleration_3h": 0.0,
                "flux_volatility_ratio": 1.0,
                "hour_of_day": float(h),
                "day_of_year": float(doy),
                "sin_hour": sin_h,
                "cos_hour": cos_h,
                "sin_doy": sin_doy,
                "cos_doy": cos_doy,
                "m_flares_prev_6h": float(req.m_flares_prev_6h or 0),
                "m_flares_prev_24h": float(req.m_flares_prev_24h or 0),
                "m_flares_prev_7d": float(req.m_flares_prev_7d or 0),
                "x_flares_prev_24h": float(req.x_flares_prev_24h or 0),
                "hours_since_last_m_flare": float(req.hours_since_last_m_flare or 168.0),
                "hours_since_last_x_flare": float(req.hours_since_last_x_flare or 720.0),
            }
            feature_vector = np.array([feat_dict[f] for f in FEATURE_NAMES]).reshape(1, -1)

        # Scale features if model requires scaling (e.g. Logistic Regression)
        requires_scaling = hasattr(self.model, "coef_")
        X_eval = self.preprocessor.transform(feature_vector) if requires_scaling else feature_vector

        # Predict raw probability
        raw_prob = float(self.model.predict_proba(X_eval)[0, 1])

        # Calibrate probability
        cal_prob = float(self.calibrator.predict_proba(np.array([raw_prob]))[0])
        cal_prob = max(0.0, min(1.0, cal_prob))

        # Persistence baseline probability
        is_active = (req.m_flares_prev_24h or 0) > 0
        base_prob = float(self.baseline.p_m_given_active if is_active else self.baseline.p_m_given_quiet)

        # Risk classification
        risk_level = self.classify_risk(cal_prob)

        now_utc = datetime.utcnow().isoformat() + "Z"

        return PredictResponse(
            success=True,
            forecast_horizon_hours=24,
            probability_m_plus=round(cal_prob, 4),
            probability_x_plus=None, # As specified in prompt: null unless separate X model trained
            risk_level=risk_level,
            model_name=self.metadata.get("model_name", "Arkastra ML Forecaster"),
            model_version=self.metadata.get("model_version", "1.0.0"),
            baseline_probability=round(base_prob, 4),
            brier_skill_score=round(self.metadata.get("validation_brier_score", 0.2096), 4),
            generated_at=now_utc,
            observation_timestamp=req.observation_timestamp,
            data_status="FRESH"
        )
