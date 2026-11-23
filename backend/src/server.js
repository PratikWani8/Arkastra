const app = require('./app');
const env = require('./config/env');
const { connectDB } = require('./config/db');
const { initCronJobs } = require('./jobs/cronJobs');

const startServer = async () => {
  await connectDB();

  // Initialize automated solar ingestion & verification cron jobs
  initCronJobs();

  const server = app.listen(env.PORT, () => {
    console.log(`[Arkastra Backend] Running on http://localhost:${env.PORT} in ${env.NODE_ENV} mode`);
    console.log(`[Arkastra Backend] REST Endpoints ready: /api/dashboard, /api/forecast, /api/solar, /api/model`);
  });

  const shutdown = async (signal) => {
    console.log(`[Arkastra Backend] Received ${signal}. Shutting down gracefully...`);
    server.close(() => {
      console.log('[Arkastra Backend] HTTP server closed.');
      process.exit(0);
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
};

if (require.main === module) {
  startServer();
}

module.exports = { startServer };
