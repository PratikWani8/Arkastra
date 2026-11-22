const express = require('express');
const router = express.Router();
const axios = require('axios');
const env = require('../config/env');
const { getDbStatus } = require('../config/db');

const getHealthData = async (req, res) => {
  let mlServiceHealth = { status: 'unknown' };
  try {
    const mlRes = await axios.get(`${env.ML_SERVICE_URL}/health`, { timeout: 2000 });
    mlServiceHealth = mlRes.data;
  } catch (error) {
    mlServiceHealth = {
      status: 'unreachable',
      error: error.message,
    };
  }

  res.json({
    status: 'healthy',
    service: 'arkastra-backend',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    database: getDbStatus(),
    mlService: mlServiceHealth,
    environment: env.NODE_ENV,
  });
};

router.get('/', getHealthData);
router.get('/health', getHealthData);

module.exports = router;
