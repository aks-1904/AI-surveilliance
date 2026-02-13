const mongoose = require('mongoose');

const alertSchema = new mongoose.Schema({
  event_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Event',
    required: true,
    index: true
  },
  alert_type: {
    type: String,
    enum: ['RESTRICTED_ENTRY', 'LOITERING', 'UNATTENDED_OBJECT'],
    required: true
  },
  priority: {
    type: String,
    enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
    required: true,
    index: true
  },
  message: {
    type: String,
    required: true
  },
  read: {
    type: Boolean,
    default: false,
    index: true
  },
  read_at: Date,
  read_by: String,
  dismissed: {
    type: Boolean,
    default: false
  },
  dismissed_at: Date,
  dismissed_by: String,
  action_taken: String
}, {
  timestamps: true
});

// Index for performance
alertSchema.index({ read: 1, dismissed: 1, createdAt: -1 });

// Method to mark as read
alertSchema.methods.markAsRead = function(user) {
  this.read = true;
  this.read_at = new Date();
  this.read_by = user || 'system';
  return this.save();
};

// Method to dismiss alert
alertSchema.methods.dismiss = function(user, action) {
  this.dismissed = true;
  this.dismissed_at = new Date();
  this.dismissed_by = user || 'system';
  if (action) this.action_taken = action;
  return this.save();
};

// Static method to get unread alerts
alertSchema.statics.getUnreadAlerts = function() {
  return this.find({ read: false, dismissed: false })
    .populate('event_id')
    .sort({ createdAt: -1 });
};

module.exports = mongoose.model('Alert', alertSchema);