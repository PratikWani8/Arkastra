const mongoose = require('mongoose');

const solarFlareEventSchema = new mongoose.Schema({
  eventId: {
    type: String,
    required: true,
    unique: true,
    index: true,
  },
  beginTime: {
    type: Date,
    required: true,
    index: true,
  },
  peakTime: {
    type: Date,
    required: true,
  },
  endTime: {
    type: Date,
  },
  flareClass: {
    type: String,
    required: true,
  },
  classCategory: {
    type: String,
    enum: ['A', 'B', 'C', 'M', 'X', 'UNKNOWN'],
    default: 'UNKNOWN',
  },
  peakFlux: {
    type: Number,
  },
  sourceLocation: {
    type: String,
  },
  source: {
    type: String,
    default: 'NASA_DONKI',
  },
  verificationStatus: {
    type: String,
    enum: ['CONFIRMED', 'UNVERIFIED'],
    default: 'CONFIRMED',
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
});

solarFlareEventSchema.index({ beginTime: -1, classCategory: 1 });

module.exports = mongoose.model('SolarFlareEvent', solarFlareEventSchema);
