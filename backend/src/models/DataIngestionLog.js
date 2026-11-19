const mongoose = require('mongoose');

const dataIngestionLogSchema = new mongoose.Schema({
  timestamp: {
    type: Date,
    default: Date.now,
  },
  source: {
    type: String,
    required: true,
  },
  recordsIngested: {
    type: Number,
    default: 0,
  },
  status: {
    type: String,
    enum: ['SUCCESS', 'WARNING', 'FAILED'],
    default: 'SUCCESS',
  },
  details: {
    type: mongoose.Schema.Types.Mixed,
  },
});

module.exports = mongoose.model('DataIngestionLog', dataIngestionLogSchema);
