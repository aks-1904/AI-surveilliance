const express = require('express');
const router = express.Router();
const Event = require('../models/Event');
const Alert = require('../models/Alert');
const { validateEvent, validatePagination, validateDateRange } = require('../middleware/validation');
const { asyncHandler } = require('../middleware/errorHandler');

/**
 * POST /api/events
 * Receive event from AI service
 */
router.post('/', validateEvent, asyncHandler(async (req, res) => {
  const { event_type, timestamp, location, details, risk_score, risk_level, metadata } = req.body;
  
  // Create event
  const event = new Event({
    event_type,
    timestamp: timestamp || new Date(),
    location,
    details,
    risk_score,
    risk_level,
    metadata
  });
  
  await event.save();
  
  // Create corresponding alert
  const alert = new Alert({
    event_id: event._id,
    alert_type: event_type,
    priority: risk_level,
    message: details?.message || `${event_type.replace('_', ' ')} detected`
  });
  
  await alert.save();
  
  // Broadcast to frontend via WebSocket
  const io = req.app.get('io');
  if (io) {
    io.emit('alert', {
      event: event.toObject(),
      alert: alert.toObject()
    });
    
    // Also emit event statistics update
    const stats = await getEventStats();
    io.emit('stats_update', stats);
  }
  
  console.log(`[EVENT RECEIVED] ${event_type} - Risk: ${risk_level} (Score: ${risk_score})`);
  
  res.status(201).json({
    success: true,
    event_id: event._id,
    alert_id: alert._id,
    timestamp: event.timestamp
  });
}));

/**
 * GET /api/events
 * Get all events with filtering and pagination
 */
router.get('/', validatePagination, validateDateRange, asyncHandler(async (req, res) => {
  const { 
    limit = 50, 
    offset = 0, 
    event_type, 
    risk_level,
    start_date,
    end_date,
    acknowledged,
    sort_by = 'timestamp',
    sort_order = 'desc'
  } = req.query;
  
  // Build query
  const query = {};
  
  if (event_type) {
    query.event_type = event_type;
  }
  
  if (risk_level) {
    query.risk_level = risk_level;
  }
  
  if (acknowledged !== undefined) {
    query.acknowledged = acknowledged === 'true';
  }
  
  if (start_date || end_date) {
    query.timestamp = {};
    if (start_date) query.timestamp.$gte = new Date(start_date);
    if (end_date) query.timestamp.$lte = new Date(end_date);
  }
  
  // Build sort
  const sortObj = {};
  sortObj[sort_by] = sort_order === 'asc' ? 1 : -1;
  
  // Execute query
  const events = await Event.find(query)
    .sort(sortObj)
    .limit(parseInt(limit))
    .skip(parseInt(offset))
    .lean();
  
  const total = await Event.countDocuments(query);
  
  res.json({
    success: true,
    events,
    pagination: {
      total,
      limit: parseInt(limit),
      offset: parseInt(offset),
      pages: Math.ceil(total / parseInt(limit))
    },
    filters: {
      event_type,
      risk_level,
      acknowledged,
      start_date,
      end_date
    }
  });
}));

/**
 * GET /api/events/:id
 * Get single event by ID
 */
router.get('/:id', asyncHandler(async (req, res) => {
  const event = await Event.findById(req.params.id);
  
  if (!event) {
    return res.status(404).json({ 
      success: false,
      error: 'Event not found',
      event_id: req.params.id
    });
  }
  
  res.json({
    success: true,
    event
  });
}));

/**
 * PUT /api/events/:id/acknowledge
 * Acknowledge an event
 */
router.put('/:id/acknowledge', asyncHandler(async (req, res) => {
  const { user, notes } = req.body;
  
  const event = await Event.findById(req.params.id);
  
  if (!event) {
    return res.status(404).json({ 
      success: false,
      error: 'Event not found',
      event_id: req.params.id
    });
  }
  
  await event.acknowledge(user);
  
  if (notes) {
    event.notes = notes;
    await event.save();
  }
  
  // Also update associated alert
  const alert = await Alert.findOne({ event_id: event._id });
  if (alert && !alert.read) {
    await alert.markAsRead(user);
  }
  
  // Broadcast update
  const io = req.app.get('io');
  if (io) {
    io.emit('event_acknowledged', {
      event_id: event._id,
      acknowledged_by: user || 'system'
    });
  }
  
  res.json({ 
    success: true, 
    event,
    message: 'Event acknowledged successfully'
  });
}));

/**
 * DELETE /api/events/:id
 * Delete an event (soft delete by marking as acknowledged)
 */
router.delete('/:id', asyncHandler(async (req, res) => {
  const event = await Event.findById(req.params.id);
  
  if (!event) {
    return res.status(404).json({ 
      success: false,
      error: 'Event not found',
      event_id: req.params.id
    });
  }
  
  // Soft delete by acknowledging
  await event.acknowledge('system');
  
  res.json({ 
    success: true,
    message: 'Event deleted successfully'
  });
}));

/**
 * GET /api/events/stats/summary
 * Get event statistics
 */
router.get('/stats/summary', asyncHandler(async (req, res) => {
  const stats = await getEventStats();
  res.json({
    success: true,
    ...stats
  });
}));

/**
 * Helper function to get event statistics
 */
async function getEventStats() {
  const now = new Date();
  const oneDayAgo = new Date(now - 24 * 60 * 60 * 1000);
  const oneHourAgo = new Date(now - 60 * 60 * 1000);
  
  const [
    totalEvents,
    todayEvents,
    lastHourEvents,
    unacknowledgedEvents,
    eventsByType,
    eventsByRisk,
    avgRiskScore
  ] = await Promise.all([
    Event.countDocuments(),
    Event.countDocuments({ timestamp: { $gte: oneDayAgo } }),
    Event.countDocuments({ timestamp: { $gte: oneHourAgo } }),
    Event.countDocuments({ acknowledged: false }),
    Event.aggregate([
      { $match: { timestamp: { $gte: oneDayAgo } } },
      { $group: { _id: '$event_type', count: { $sum: 1 } } }
    ]),
    Event.aggregate([
      { $match: { timestamp: { $gte: oneDayAgo } } },
      { $group: { _id: '$risk_level', count: { $sum: 1 } } }
    ]),
    Event.aggregate([
      { $match: { timestamp: { $gte: oneDayAgo } } },
      { $group: { _id: null, avgRisk: { $avg: '$risk_score' } } }
    ])
  ]);
  
  return {
    total_events: totalEvents,
    today_events: todayEvents,
    last_hour_events: lastHourEvents,
    unacknowledged_events: unacknowledgedEvents,
    average_risk_score: avgRiskScore[0]?.avgRisk || 0,
    events_by_type: eventsByType,
    events_by_risk: eventsByRisk
  };
}

module.exports = router;