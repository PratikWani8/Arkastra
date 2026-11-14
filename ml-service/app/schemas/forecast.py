"""
Pydantic schemas for the Arkastra ML Prediction Service.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ObservationItem(BaseModel):
    timestamp: str = Field(..., description="ISO UTC timestamp of the observation")
    long_flux: float = Field(..., ge=0.0, description="GOES Long wavelength flux 0.1-0.8nm in W/m^2")
    short_flux: Optional[float] = Field(None, ge=0.0, description="GOES Short wavelength flux 0.05-0.4nm in W/m^2")

class PredictRequest(BaseModel):
    observation_timestamp: str = Field(..., description="ISO UTC timestamp of current observation")
    current_long_flux: float = Field(..., gt=0.0, description="Current GOES 0.1-0.8nm flux in W/m^2")
    current_short_flux: Optional[float] = Field(None, gt=0.0, description="Current GOES 0.05-0.4nm flux in W/m^2")
    m_flares_prev_6h: Optional[int] = Field(0, ge=0, description="Count of M+ flares in previous 6 hours")
    m_flares_prev_24h: Optional[int] = Field(0, ge=0, description="Count of M+ flares in previous 24 hours")
    m_flares_prev_7d: Optional[int] = Field(0, ge=0, description="Count of M+ flares in previous 7 days")
    x_flares_prev_24h: Optional[int] = Field(0, ge=0, description="Count of X flares in previous 24 hours")
    hours_since_last_m_flare: Optional[float] = Field(168.0, ge=0.0, description="Hours elapsed since last M+ flare")
    hours_since_last_x_flare: Optional[float] = Field(720.0, ge=0.0, description="Hours elapsed since last X flare")
    rolling_observations: Optional[List[ObservationItem]] = Field(None, description="Recent rolling observation history for exact feature extraction")

class PredictResponse(BaseModel):
    success: bool
    forecast_horizon_hours: int = 24
    probability_m_plus: float = Field(..., ge=0.0, le=1.0)
    probability_x_plus: Optional[float] = None
    risk_level: str
    model_name: str
    model_version: str
    baseline_probability: float
    brier_skill_score: Optional[float] = None
    generated_at: str
    observation_timestamp: str
    data_status: str
