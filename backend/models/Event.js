const mongoose = require('mongoose');

const eventSchema = new mongoose.Schema({
  event_type: {
    type: String,
    enum: ['RESTRICTED_ENTRY', 'LOITERING', 'UNATTENDED_OBJECT'],
    required: true,
    index: true
  },
  timestamp: {
    type: Date,
    required: true,
    default: Date.now,
    index: true
  },
  location: {
    x: { type: Number },
    y: { type: Number }
  },
  details: {
    message: String,
    bbox: [Number],
    person_id: Number,
    object_id: Number,
    zone_id: Number,
    zone_name: String,
    duration: Number,
    start_time: Date
  },
  risk_score: {
    type: Number,
    required: true,
    min: 0,
    max: 10
  },
  risk_level: {
    type: String,
    enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
    required: true,
    index: true
  },
  metadata: {
    person_id: Number,
    object_id: Number,
    zone_id: Number,
    duration: Number,
    confidence: Number
  },
  acknowledged: {
    type: Boolean,
    default: false,
    index: true
  },
  acknowledged_at: Date,
  acknowledged_by: String,
  notes: String
}, {
  timestamps: true
});

// Indexes for performance
eventSchema.index({ timestamp: -1 });
eventSchema.index({ event_type: 1, timestamp: -1 });
eventSchema.index({ risk_level: 1, acknowledged: 1 });

// Virtual for formatted timestamp
eventSchema.virtual('formatted_time').get(function() {
  return this.timestamp.toLocaleString();
});

// Method to acknowledge event
eventSchema.methods.acknowledge = function(user) {
  this.acknowledged = true;
  this.acknowledged_at = new Date();
  this.acknowledged_by = user || 'system';
  return this.save();
};

module.exports = mongoose.model('Event', eventSchema);