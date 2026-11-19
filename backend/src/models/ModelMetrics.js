const mongoose = require('mongoose');

const modelMetricsSchema = new mongoose.Schema({
  evaluatedAt: {
    type: Date,
    default: Date.now,
  },
  modelVersion: {
    type: String,
    required: true,
  },
  modelName: {
    type: String,
    required: true,
  },
  brierScore: {
    type: Number,
    required: true,
  },
  baselineBrierScore: {
    type: Number,
    required: true,
  },
  brierSkillScore: {
    type: Number,
    required: true,
  },
  tss: {
    type: Number,
    required: true,
  },
  rocAuc: {
    type: Number,
    required: true,
  },
  prAuc: {
    type: Number,
    required: true,
  },
  metricsData: {
    type: mongoose.Schema.Types.Mixed,
  },
});

module.exports = mongoose.model('ModelMetrics', modelMetricsSchema);
