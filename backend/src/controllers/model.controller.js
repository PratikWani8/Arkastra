const fs = require('fs');
const path = require('path');
const axios = require('axios');
const env = require('../config/env');

const reportsDir = path.resolve(__dirname, '..', '..', '..', 'ml-service', 'reports');
const modelsDir = path.resolve(__dirname, '..', '..', '..', 'models');

exports.getMetrics = async (req, res) => {
  // First attempt from FastAPI
  try {
    const resp = await axios.get(`${env.ML_SERVICE_URL}/metrics`, { timeout: 2000 });
    return res.json(resp.data);
  } catch (e) {
    // Fallback to local report file
    const filePath = path.join(reportsDir, 'model_evaluation.json');
    if (fs.existsSync(filePath)) {
      return res.json(JSON.parse(fs.readFileSync(filePath, 'utf8')));
    }
    res.status(404).json({ success: false, message: 'Model evaluation metrics not found' });
  }
};

exports.getCalibration = async (req, res) => {
  const filePath = path.join(reportsDir, 'calibration_report.json');
  if (fs.existsSync(filePath)) {
    return res.json(JSON.parse(fs.readFileSync(filePath, 'utf8')));
  }
  res.status(404).json({ success: false, message: 'Calibration report not found' });
};

exports.getBaselineComparison = async (req, res) => {
  // First attempt from FastAPI
  try {
    const resp = await axios.get(`${env.ML_SERVICE_URL}/baseline`, { timeout: 2000 });
    const baselineParams = resp.data;
    const compPath = path.join(reportsDir, 'baseline_comparison.json');
    let compData = {};
    if (fs.existsSync(compPath)) {
      compData = JSON.parse(fs.readFileSync(compPath, 'utf8'));
    }
    return res.json({ success: true, baselineParameters: baselineParams, ...compData });
  } catch (e) {
    const compPath = path.join(reportsDir, 'baseline_comparison.json');
    if (fs.existsSync(compPath)) {
      return res.json(JSON.parse(fs.readFileSync(compPath, 'utf8')));
    }
    res.status(404).json({ success: false, message: 'Baseline comparison not found' });
  }
};

exports.getMetadata = async (req, res) => {
  const metaPath = path.join(modelsDir, 'arkastra_model_metadata.json');
  if (fs.existsSync(metaPath)) {
    return res.json(JSON.parse(fs.readFileSync(metaPath, 'utf8')));
  }
  res.status(404).json({ success: false, message: 'Model metadata not found' });
};

exports.getFeatureImportance = async (req, res) => {
  const fiPath = path.join(reportsDir, 'feature_importance.json');
  if (fs.existsSync(fiPath)) {
    return res.json(JSON.parse(fs.readFileSync(fiPath, 'utf8')));
  }
  res.status(404).json({ success: false, message: 'Feature importance report not found' });
};
