"""
ARKASTRA: FastAPI Machine Learning Service
Exposes trained, calibrated space weather ML models and persistence baselines:
- POST /predict: Live 24-hour calibrated solar flare probability prediction
- GET /health: Service and model state health checks
- GET /metrics: Scientific model evaluation metrics (Brier, BSS, TSS, ROC-AUC)
- GET /baseline: Persistence baseline parameters and priors
- GET /model/metadata: Model architecture, training period, and dataset provenance
- GET /model/feature-importance: Explainability feature importances
"""

import os
import sys
import json
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Ensure path includes ml-service root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.schemas.forecast import PredictRequest, PredictResponse
from app.services.forecaster import SolarForecaster

# Initialize forecaster at module level
forecaster = SolarForecaster(models_dir=settings.MODELS_DIR)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Arkastra Calibrated Solar Flare Probability Forecasting Service"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    is_loaded = forecaster.is_ready if forecaster else False
    version = forecaster.metadata.get("model_version", "1.0.0") if (forecaster and forecaster.is_ready) else "none"
    model_name = forecaster.metadata.get("model_name", "Arkastra Solar Forecaster") if (forecaster and forecaster.is_ready) else "none"
    
    return {
        "status": "healthy",
        "service": "arkastra-ml-service",
        "python_version": sys.version.split(" ")[0],
        "model_loaded": is_loaded,
        "available_model_version": version,
        "model_name": model_name
    }

@app.post("/predict", response_model=PredictResponse)
def predict_flare_probability(request: PredictRequest):
    if not forecaster or not forecaster.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Arkastra ML model artifacts are not ready or not loaded."
        )
    try:
        response = forecaster.forecast(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inference failure: {str(e)}"
        )

@app.get("/metrics")
def get_metrics():
    eval_path = os.path.join(settings.REPORTS_DIR, "model_evaluation.json")
    if not os.path.exists(eval_path):
        raise HTTPException(status_code=404, detail="Evaluation metrics report not found.")
    with open(eval_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/baseline")
def get_baseline_parameters():
    baseline_path = os.path.join(settings.MODELS_DIR, "arkastra_persistence_baseline.json")
    if not os.path.exists(baseline_path):
        raise HTTPException(status_code=404, detail="Baseline parameters file not found.")
    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/model/metadata")
def get_model_metadata():
    meta_path = os.path.join(settings.MODELS_DIR, "arkastra_model_metadata.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Model metadata file not found.")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/model/feature-importance")
def get_feature_importance():
    fi_path = os.path.join(settings.REPORTS_DIR, "feature_importance.json")
    if not os.path.exists(fi_path):
        raise HTTPException(status_code=404, detail="Feature importance report not found.")
    with open(fi_path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
