const mongoose = require('mongoose');

const zoneSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true,
    unique: true
  },
  polygon: [{
    x: { type: Number, required: true },
    y: { type: Number, required: true }
  }],
  active: {
    type: Boolean,
    default: true,
    index: true
  },
  created_by: {
    type: String,
    default: 'system'
  },
  description: {
    type: String,
    trim: true
  },
  color: {
    type: String,
    default: '#FF0000'
  },
  risk_multiplier: {
    type: Number,
    default: 1.0,
    min: 0.1,
    max: 3.0
  }
}, {
  timestamps: true
});

// Validate polygon has at least 3 points
zoneSchema.pre('save', function(next) {
  if (this.polygon.length < 3) {
    next(new Error('Zone must have at least 3 points'));
  } else {
    next();
  }
});

// Method to deactivate zone
zoneSchema.methods.deactivate = function() {
  this.active = false;
  return this.save();
};

// Method to activate zone
zoneSchema.methods.activate = function() {
  this.active = true;
  return this.save();
};

// Static method to get active zones
zoneSchema.statics.getActiveZones = function() {
  return this.find({ active: true });
};

module.exports = mongoose.model('Zone', zoneSchema);