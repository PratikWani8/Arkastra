const mongoose = require('mongoose');

const forecastSchema = new mongoose.Schema({
  generatedAt: {
    type: Date,
    default: Date.now,
    index: true,
  },
  observationTimestamp: {
    type: Date,
    required: true,
    index: true,
  },
  forecastHorizonHours: {
    type: Number,
    default: 24,
  },
  probabilityMPlus: {
    type: Number,
    required: true,
    min: 0.0,
    max: 1.0,
  },
  probabilityXPlus: {
    type: Number,
    default: null,
  },
  riskLevel: {
    type: String,
    enum: ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'],
    required: true,
    index: true,
  },
  modelVersion: {
    type: String,
    default: '1.0.0',
  },
  modelName: {
    type: String,
    default: 'Arkastra Solar Forecaster',
  },
  baselineProbability: {
    type: Number,
    required: true,
  },
  brierSkillScore: {
    type: Number,
  },
  dataFreshness: {
    type: String,
    enum: ['FRESH', 'STALE', 'UNAVAILABLE'],
    default: 'FRESH',
  },
  actualOutcome: {
    type: Boolean,
    default: null,
  },
  verificationStatus: {
    type: String,
    enum: ['PENDING', 'VERIFIED_POSITIVE', 'VERIFIED_NEGATIVE', 'UNVERIFIED'],
    default: 'PENDING',
    index: true,
  },
  verifiedAt: {
    type: Date,
  },
});

forecastSchema.index({ generatedAt: -1, riskLevel: 1 });

module.exports = mongoose.model('Forecast', forecastSchema);
