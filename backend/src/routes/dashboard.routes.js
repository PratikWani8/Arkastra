const express = require('express');
const router = express.Router();
const {
  getOverview,
  getCurrentFlux,
  getForecast,
  getRecentEvents,
} = require('../controllers/dashboard.controller');

router.get('/overview', getOverview);
router.get('/current-flux', getCurrentFlux);
router.get('/forecast', getForecast);
router.get('/recent-events', getRecentEvents);

module.exports = router;
