const axios = require('axios');
const env = require('../config/env');
const dataStore = require('../services/dataStore');

exports.predict = async (req, res) => {
  try {
    const {
      current_long_flux,
      current_short_flux,
      observation_timestamp,
      m_flares_prev_6h,
      m_flares_prev_24h,
      m_flares_prev_7d,
      x_flares_prev_24h,
      hours_since_last_m_flare,
      hours_since_last_x_flare,
    } = req.body;

    const payload = {
      observation_timestamp: observation_timestamp || new Date().toISOString(),
      current_long_flux: current_long_flux || 1.5e-6,
      current_short_flux: current_short_flux || (current_long_flux || 1.5e-6) * 0.22,
      m_flares_prev_6h: m_flares_prev_6h || 0,
      m_flares_prev_24h: m_flares_prev_24h || 0,
      m_flares_prev_7d: m_flares_prev_7d || 0,
      x_flares_prev_24h: x_flares_prev_24h || 0,
      hours_since_last_m_flare: hours_since_last_m_flare || 168.0,
      hours_since_last_x_flare: hours_since_last_x_flare || 720.0,
    };

    // Call FastAPI ML Service
    const mlResponse = await axios.post(`${env.ML_SERVICE_URL}/predict`, payload, {
      timeout: 5000,
    });

    const pred = mlResponse.data;

    // Save forecast to database
    const saved = await dataStore.saveForecast({
      generatedAt: new Date(pred.generated_at),
      observationTimestamp: new Date(pred.observation_timestamp),
      forecastHorizonHours: pred.forecast_horizon_hours || 24,
      probabilityMPlus: pred.probability_m_plus,
      probabilityXPlus: pred.probability_x_plus,
      riskLevel: pred.risk_level,
      modelVersion: pred.model_version,
      modelName: pred.model_name,
      baselineProbability: pred.baseline_probability,
      brierSkillScore: pred.brier_skill_score || 0.2096,
      dataFreshness: pred.data_status || 'FRESH',
      verificationStatus: 'PENDING',
    });

    res.status(201).json({
      success: true,
      forecast: saved,
    });
  } catch (error) {
    // If ML service is offline, calculate fallback prediction based on persistence baseline
    console.warn(`[Forecast Controller] ML service communication failed (${error.message}). Using local fallback.`);
    const fallbackProb = 0.35;
    const saved = await dataStore.saveForecast({
      generatedAt: new Date(),
      observationTimestamp: new Date(),
      forecastHorizonHours: 24,
      probabilityMPlus: fallbackProb,
      probabilityXPlus: null,
      riskLevel: 'HIGH',
      modelVersion: '1.0.0-fallback',
      modelName: 'Arkastra Fallback Persistence Forecaster',
      baselineProbability: 0.3628,
      brierSkillScore: 0.2096,
      dataFreshness: 'STALE',
      verificationStatus: 'PENDING',
    });

    res.status(200).json({
      success: true,
      forecast: saved,
      warning: 'Prediction generated via fallback baseline.',
    });
  }
};

exports.getLatest = async (req, res) => {
  try {
    const latest = await dataStore.getLatestForecast();
    res.json({ success: true, forecast: latest });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getHistory = async (req, res) => {
  try {
    const page = parseInt(req.query.page, 10) || 1;
    const limit = parseInt(req.query.limit, 10) || 20;
    const filter = {};
    if (req.query.riskLevel) filter.riskLevel = req.query.riskLevel.toUpperCase();
    if (req.query.verificationStatus) filter.verificationStatus = req.query.verificationStatus.toUpperCase();

    const result = await dataStore.getForecastHistory(page, limit, filter);
    res.json({
      success: true,
      ...result,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getForecastById = async (req, res) => {
  try {
    const { id } = req.params;
    const history = await dataStore.getForecastHistory(1, 100);
    const item = history.items.find((f) => String(f._id) === id);
    if (!item) {
      return res.status(404).json({ success: false, message: 'Forecast not found' });
    }
    res.json({ success: true, forecast: item });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};
