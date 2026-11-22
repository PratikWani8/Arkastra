const mongoose = require('mongoose');

const solarObservationSchema = new mongoose.Schema({
  timestamp: {
    type: Date,
    required: true,
    index: true,
  },
  satelliteId: {
    type: Number,
    required: true,
    default: 16,
  },
  shortFlux: {
    type: Number,
    required: true,
  },
  longFlux: {
    type: Number,
    required: true,
  },
  ratio: {
    type: Number,
  },
  source: {
    type: String,
    default: 'NOAA_SWPC_GOES',
  },
  qualityStatus: {
    type: String,
    enum: ['GOOD', 'QUESTIONABLE', 'BAD', 'MISSING'],
    default: 'GOOD',
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
});

solarObservationSchema.index({ timestamp: -1, satelliteId: 1 });

module.exports = mongoose.model('SolarObservation', solarObservationSchema);
