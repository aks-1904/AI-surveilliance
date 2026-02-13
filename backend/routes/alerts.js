const express = require('express');
const router = express.Router();
const Alert = require('../models/Alert');
const { asyncHandler } = require('../middleware/errorHandler');

/**
 * GET /api/alerts
 * Get all alerts with filtering
 */
router.get('/', asyncHandler(async (req, res) => {
  const { 
    read, 
    dismissed, 
    priority, 
    limit = 50, 
    offset = 0 
  } = req.query;
  
  const query = {};
  
  if (read !== undefined) {
    query.read = read === 'true';
  }
  
  if (dismissed !== undefined) {
    query.dismissed = dismissed === 'true';
  }
  
  if (priority) {
    query.priority = priority;
  }
  
  const alerts = await Alert.find(query)
    .populate('event_id')
    .sort({ createdAt: -1 })
    .limit(parseInt(limit))
    .skip(parseInt(offset));
  
  const total = await Alert.countDocuments(query);
  
  res.json({
    success: true,
    alerts,
    total,
    limit: parseInt(limit),
    offset: parseInt(offset)
  });
}));

/**
 * GET /api/alerts/unread
 * Get all unread alerts
 */
router.get('/unread', asyncHandler(async (req, res) => {
  const alerts = await Alert.getUnreadAlerts();
  
  res.json({
    success: true,
    count: alerts.length,
    alerts
  });
}));

/**
 * PUT /api/alerts/:id/read
 * Mark alert as read
 */
router.put('/:id/read', asyncHandler(async (req, res) => {
  const { user } = req.body;
  
  const alert = await Alert.findById(req.params.id);
  
  if (!alert) {
    return res.status(404).json({
      success: false,
      error: 'Alert not found'
    });
  }
  
  await alert.markAsRead(user);
  
  // Broadcast update
  const io = req.app.get('io');
  if (io) {
    io.emit('alert_read', { alert_id: alert._id });
  }
  
  res.json({
    success: true,
    alert
  });
}));

/**
 * PUT /api/alerts/:id/dismiss
 * Dismiss an alert
 */
router.put('/:id/dismiss', asyncHandler(async (req, res) => {
  const { user, action } = req.body;
  
  const alert = await Alert.findById(req.params.id);
  
  if (!alert) {
    return res.status(404).json({
      success: false,
      error: 'Alert not found'
    });
  }
  
  await alert.dismiss(user, action);
  
  // Broadcast update
  const io = req.app.get('io');
  if (io) {
    io.emit('alert_dismissed', { alert_id: alert._id });
  }
  
  res.json({
    success: true,
    alert
  });
}));

/**
 * POST /api/alerts/mark-all-read
 * Mark all alerts as read
 */
router.post('/mark-all-read', asyncHandler(async (req, res) => {
  const { user } = req.body;
  
  const result = await Alert.updateMany(
    { read: false },
    { 
      read: true, 
      read_at: new Date(),
      read_by: user || 'system'
    }
  );
  
  // Broadcast update
  const io = req.app.get('io');
  if (io) {
    io.emit('all_alerts_read');
  }
  
  res.json({
    success: true,
    marked_read: result.modifiedCount
  });
}));

module.exports = router;