const express = require('express');
const router = express.Router();
const { getObservations, getFlux, getEvents } = require('../controllers/solar.controller');

router.get('/observations', getObservations);
router.get('/flux', getFlux);
router.get('/events', getEvents);

module.exports = router;
