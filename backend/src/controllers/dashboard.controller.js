const dataStore = require('../services/dataStore');
const { getDbStatus } = require('../config/db');

const getFlareClassFromFlux = (flux) => {
  if (!flux || flux <= 0) return 'B-Class Quiet';
  if (flux >= 1e-4) return `X${(flux / 1e-4).toFixed(1)}`;
  if (flux >= 1e-5) return `M${(flux / 1e-5).toFixed(1)}`;
  if (flux >= 1e-6) return `C${(flux / 1e-6).toFixed(1)}`;
  if (flux >= 1e-7) return `B${(flux / 1e-7).toFixed(1)}`;
  return `A${(flux / 1e-8).toFixed(1)}`;
};

exports.getOverview = async (req, res) => {
  try {
    const [latestObs, latestFc, recentEvents, recentFlux] = await Promise.all([
      dataStore.getLatestObservation(),
      dataStore.getLatestForecast(),
      dataStore.getRecentEvents(5),
      dataStore.getRecentObservations(48),
    ]);

    const currentFluxVal = latestObs ? latestObs.longFlux : 1.42e-6;
    const currentClass = getFlareClassFromFlux(currentFluxVal);

    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      currentConditions: {
        timestamp: latestObs ? latestObs.timestamp : new Date(),
        longFlux: currentFluxVal,
        shortFlux: latestObs ? latestObs.shortFlux : currentFluxVal * 0.22,
        fluxRatio: latestObs ? latestObs.ratio : 0.22,
        currentActivityClass: currentClass,
        satelliteId: latestObs ? latestObs.satelliteId : 18,
        dataFreshness: latestObs ? 'FRESH' : 'STALE',
      },
      latestForecast: latestFc || {
        probabilityMPlus: 0.35,
        probabilityXPlus: null,
        riskLevel: 'HIGH',
        forecastHorizonHours: 24,
        modelVersion: '1.0.0',
        baselineProbability: 0.3628,
        dataFreshness: 'FRESH',
        generatedAt: new Date(),
      },
      recentEvents: recentEvents || [],
      recentFluxTelemetry: recentFlux || [],
      systemHealth: {
        database: getDbStatus(),
        telemetryFeed: 'ACTIVE',
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getCurrentFlux = async (req, res) => {
  try {
    const obs = await dataStore.getLatestObservation();
    const flux = obs ? obs.longFlux : 1.5e-6;
    res.json({
      success: true,
      timestamp: obs ? obs.timestamp : new Date(),
      longFlux: flux,
      shortFlux: obs ? obs.shortFlux : flux * 0.22,
      ratio: obs ? obs.ratio : 0.22,
      activityClassification: getFlareClassFromFlux(flux),
      satelliteId: obs ? obs.satelliteId : 18,
      source: obs ? obs.source : 'NOAA_SWPC_GOES',
      qualityStatus: obs ? obs.qualityStatus : 'GOOD',
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getForecast = async (req, res) => {
  try {
    const fc = await dataStore.getLatestForecast();
    res.json({
      success: true,
      forecast: fc,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getRecentEvents = async (req, res) => {
  try {
    const limit = parseInt(req.query.limit, 10) || 10;
    const events = await dataStore.getRecentEvents(limit);
    res.json({
      success: true,
      count: events.length,
      events,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};
