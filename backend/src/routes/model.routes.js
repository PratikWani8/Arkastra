const express = require('express');
const router = express.Router();
const {
  getMetrics,
  getCalibration,
  getBaselineComparison,
  getMetadata,
  getFeatureImportance,
} = require('../controllers/model.controller');

router.get('/metrics', getMetrics);
router.get('/calibration', getCalibration);
router.get('/baseline-comparison', getBaselineComparison);
router.get('/metadata', getMetadata);
router.get('/feature-importance', getFeatureImportance);

module.exports = router;
