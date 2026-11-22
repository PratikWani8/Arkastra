/*
 * ARKASTRA: Forecast Verification Service
 * Compares elapsed 24-hour forecast windows against authentic recorded solar flare events:
 * - Checks if at least one M-class or stronger flare occurred in (T_obs, T_obs + 24h]
 * - Assigns deterministic ground truth actualOutcome (true / false)
 * - Updates verificationStatus (VERIFIED_POSITIVE / VERIFIED_NEGATIVE)
 * - Preserves immutable original probability forecasts
 */

const dataStore = require('./dataStore');
const Forecast = require('../models/Forecast');
const SolarFlareEvent = require('../models/SolarFlareEvent');
const mongoose = require('mongoose');

const verifyElapsedForecasts = async () => {
  try {
    const isDbActive = mongoose.connection.readyState === 1;
    const now = new Date();
    const horizonMs = 24 * 3600 * 1000;

    let pendingForecasts = [];
    if (isDbActive) {
      // Find forecasts whose 24h horizon has completely elapsed and status is still PENDING
      const cutoff = new Date(now.getTime() - horizonMs);
      pendingForecasts = await Forecast.find({
        observationTimestamp: { $lte: cutoff },
        verificationStatus: 'PENDING',
      }).limit(50);
    } else {
      const history = await dataStore.getForecastHistory(1, 100, { verificationStatus: 'PENDING' });
      pendingForecasts = history.items.filter(
        (f) => new Date(f.observationTimestamp).getTime() + horizonMs <= now.getTime()
      );
    }

    if (pendingForecasts.length === 0) {
      return { verifiedCount: 0, message: 'No pending forecasts require verification.' };
    }

    console.log(`[Verification] Verifying ${pendingForecasts.length} elapsed forecasts...`);
    const allEvents = await dataStore.getRecentEvents(500);

    let verifiedCount = 0;
    for (const fc of pendingForecasts) {
      const obsTime = new Date(fc.observationTimestamp).getTime();
      const horizonEnd = obsTime + horizonMs;

      // Look for M+ flares occurring strictly within (obsTime, horizonEnd]
      const flareOccurred = allEvents.some((ev) => {
        const evTime = new Date(ev.beginTime).getTime();
        const isMPlus = ev.classCategory === 'M' || ev.classCategory === 'X';
        return isMPlus && evTime > obsTime && evTime <= horizonEnd;
      });

      const outcome = flareOccurred;
      const status = flareOccurred ? 'VERIFIED_POSITIVE' : 'VERIFIED_NEGATIVE';

      if (isDbActive && fc._id) {
        await Forecast.findByIdAndUpdate(fc._id, {
          actualOutcome: outcome,
          verificationStatus: status,
          verifiedAt: new Date(),
        });
      } else {
        fc.actualOutcome = outcome;
        fc.verificationStatus = status;
        fc.verifiedAt = new Date();
      }

      verifiedCount++;
    }

    console.log(`[Verification] Completed verification for ${verifiedCount} forecasts.`);
    return { verifiedCount };
  } catch (error) {
    console.error(`[Verification Error] ${error.message}`);
    return { error: error.message };
  }
};

module.exports = { verifyElapsedForecasts };
