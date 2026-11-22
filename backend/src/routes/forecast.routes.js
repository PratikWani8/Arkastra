const express = require('express');
const router = express.Router();
const {
  predict,
  getLatest,
  getHistory,
  getForecastById,
} = require('../controllers/forecast.controller');

router.post('/predict', predict);
router.get('/latest', getLatest);
router.get('/history', getHistory);
router.get('/:id', getForecastById);

module.exports = router;
