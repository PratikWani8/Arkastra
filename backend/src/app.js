const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const env = require('./config/env');
const path = require('path');
const { notFound, errorHandler } = require('./middleware/errorHandler');

// Route Imports
const healthRoutes = require('./routes/health.routes');
const authRoutes = require('./routes/auth.routes');
const dashboardRoutes = require('./routes/dashboard.routes');
const solarRoutes = require('./routes/solar.routes');
const forecastRoutes = require('./routes/forecast.routes');
const modelRoutes = require('./routes/model.routes');

const app = express();

// Security and utility middleware
app.use(helmet());
app.use(cors({
  origin: [env.CORS_ORIGIN, 'http://localhost:5173', 'http://127.0.0.1:5173'],
  credentials: true,
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 300,
  standardHeaders: true,
  legacyHeaders: false,
  message: { success: false, message: 'Too many requests, please try again later.' },
});
app.use('/api/', limiter);

app.use(morgan(env.NODE_ENV === 'production' ? 'combined' : 'dev'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Health Routes
app.use('/health', healthRoutes);
app.use('/api/health', healthRoutes);

// API Route Mounts
app.use('/api/reports/figures', express.static(path.join(__dirname, '../../ml-service/reports/figures')));
app.use('/api/auth', authRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/solar', solarRoutes);
app.use('/api/forecast', forecastRoutes);
app.use('/api/model', modelRoutes);

// Root route
app.get('/', (req, res) => {
  res.json({
    name: 'Arkastra Solar Flare Forecasting Backend',
    status: 'online',
    version: '1.0.0',
    endpoints: {
      health: '/api/health',
      dashboard: '/api/dashboard/overview',
      solar: '/api/solar/flux',
      forecast: '/api/forecast/latest',
      model: '/api/model/metrics',
    },
  });
});

// Centralized error handling
app.use(notFound);
app.use(errorHandler);

module.exports = app;
