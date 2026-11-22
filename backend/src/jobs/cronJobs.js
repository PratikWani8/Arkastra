const cron = require('node-cron');
const { fetchAndIngestLiveFlux } = require('../services/solarIngestionService');
const { verifyElapsedForecasts } = require('../services/forecastVerificationService');

const initCronJobs = () => {
  console.log('[Scheduler] Initializing automated space weather cron jobs...');

  // 1. Live Solar Ingestion: Poll NOAA SWPC every 5 minutes
  cron.schedule('*/5 * * * *', async () => {
    console.log('[Scheduler] Executing scheduled live NOAA GOES flux ingestion...');
    await fetchAndIngestLiveFlux();
  });

  // 2. Forecast Outcome Verification: Run every 30 minutes
  cron.schedule('*/30 * * * *', async () => {
    console.log('[Scheduler] Executing scheduled 24h forecast verification pass...');
    await verifyElapsedForecasts();
  });

  // Execute initial verification pass on startup
  setTimeout(async () => {
    console.log('[Scheduler] Running initial startup verification and sync pass...');
    await verifyElapsedForecasts();
  }, 3000);
};

module.exports = { initCronJobs };
