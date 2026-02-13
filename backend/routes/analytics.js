const express = require('express');
const router = express.Router();
const Event = require('../models/Event');
const Alert = require('../models/Alert');
const Zone = require('../models/Zone');
const { asyncHandler } = require('../middleware/errorHandler');

/**
 * GET /api/analytics/summary
 * Get comprehensive analytics summary
 */
router.get('/summary', asyncHandler(async (req, res) => {
  const { hours = 24 } = req.query;
  const hoursNum = parseInt(hours);
  
  const now = new Date();
  const startDate = new Date(now - hoursNum * 60 * 60 * 1000);
  
  const [
    totalEvents,
    eventsByType,
    riskDistribution,
    avgRiskScore,
    unacknowledgedCount,
    activeZones,
    unreadAlerts
  ] = await Promise.all([
    // Total events in period
    Event.countDocuments({ timestamp: { $gte: startDate } }),
    
    // Events by type
    Event.aggregate([
      { $match: { timestamp: { $gte: startDate } } },
      { $group: { _id: '$event_type', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]),
    
    // Risk level distribution
    Event.aggregate([
      { $match: { timestamp: { $gte: startDate } } },
      { $group: { _id: '$risk_level', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]),
    
    // Average risk score
    Event.aggregate([
      { $match: { timestamp: { $gte: startDate } } },
      { $group: { _id: null, avgRisk: { $avg: '$risk_score' }, maxRisk: { $max: '$risk_score' } } }
    ]),
    
    // Unacknowledged events
    Event.countDocuments({ 
      timestamp: { $gte: startDate },
      acknowledged: false 
    }),
    
    // Active zones count
    Zone.countDocuments({ active: true }),
    
    // Unread alerts count
    Alert.countDocuments({ read: false, dismissed: false })
  ]);
  
  // Format events by type
  const eventTypeMap = {};
  eventsByType.forEach(item => {
    eventTypeMap[item._id] = item.count;
  });
  
  // Format risk distribution
  const riskMap = {};
  riskDistribution.forEach(item => {
    riskMap[item._id] = item.count;
  });
  
  res.json({
    success: true,
    period: `${hoursNum}h`,
    timestamp: now,
    summary: {
      total_events: totalEvents,
      unacknowledged_events: unacknowledgedCount,
      average_risk_score: avgRiskScore[0]?.avgRisk?.toFixed(2) || 0,
      max_risk_score: avgRiskScore[0]?.maxRisk || 0,
      active_zones: activeZones,
      unread_alerts: unreadAlerts
    },
    events_by_type: {
      RESTRICTED_ENTRY: eventTypeMap.RESTRICTED_ENTRY || 0,
      LOITERING: eventTypeMap.LOITERING || 0,
      UNATTENDED_OBJECT: eventTypeMap.UNATTENDED_OBJECT || 0
    },
    risk_distribution: {
      LOW: riskMap.LOW || 0,
      MEDIUM: riskMap.MEDIUM || 0,
      HIGH: riskMap.HIGH || 0,
      CRITICAL: riskMap.CRITICAL || 0
    }
  });
}));

/**
 * GET /api/analytics/timeline
 * Get hourly event timeline
 */
router.get('/timeline', asyncHandler(async (req, res) => {
  const { hours = 24 } = req.query;
  const hoursNum = parseInt(hours);
  
  const startDate = new Date(Date.now() - hoursNum * 60 * 60 * 1000);
  
  const timeline = await Event.aggregate([
    {
      $match: { timestamp: { $gte: startDate } }
    },
    {
      $group: {
        _id: {
          $dateToString: {
            format: '%Y-%m-%d %H:00',
            date: '$timestamp'
          }
        },
        count: { $sum: 1 },
        avg_risk: { $avg: '$risk_score' },
        max_risk: { $max: '$risk_score' },
        events_by_type: {
          $push: '$event_type'
        }
      }
    },
    {
      $project: {
        timestamp: '$_id',
        count: 1,
        avg_risk: { $round: ['$avg_risk', 2] },
        max_risk: 1,
        restricted_entry: {
          $size: {
            $filter: {
              input: '$events_by_type',
              cond: { $eq: ['$$this', 'RESTRICTED_ENTRY'] }
            }
          }
        },
        loitering: {
          $size: {
            $filter: {
              input: '$events_by_type',
              cond: { $eq: ['$$this', 'LOITERING'] }
            }
          }
        },
        unattended_object: {
          $size: {
            $filter: {
              input: '$events_by_type',
              cond: { $eq: ['$$this', 'UNATTENDED_OBJECT'] }
            }
          }
        }
      }
    },
    {
      $sort: { timestamp: 1 }
    }
  ]);
  
  res.json({
    success: true,
    period: `${hoursNum}h`,
    data_points: timeline.length,
    timeline
  });
}));

/**
 * GET /api/analytics/heatmap
 * Get location-based heatmap data
 */
router.get('/heatmap', asyncHandler(async (req, res) => {
  const { hours = 24, grid_size = 50 } = req.query;
  const hoursNum = parseInt(hours);
  const gridSize = parseInt(grid_size);
  
  const startDate = new Date(Date.now() - hoursNum * 60 * 60 * 1000);
  
  const events = await Event.find({
    timestamp: { $gte: startDate },
    'location.x': { $exists: true },
    'location.y': { $exists: true }
  }).select('location event_type risk_score');
  
  // Create heatmap grid
  const heatmap = {};
  
  events.forEach(event => {
    const gridX = Math.floor(event.location.x / gridSize);
    const gridY = Math.floor(event.location.y / gridSize);
    const key = `${gridX},${gridY}`;
    
    if (!heatmap[key]) {
      heatmap[key] = {
        x: gridX * gridSize,
        y: gridY * gridSize,
        count: 0,
        total_risk: 0,
        events: []
      };
    }
    
    heatmap[key].count++;
    heatmap[key].total_risk += event.risk_score;
    heatmap[key].events.push(event.event_type);
  });
  
  // Convert to array and calculate averages
  const heatmapArray = Object.values(heatmap).map(cell => ({
    x: cell.x,
    y: cell.y,
    count: cell.count,
    avg_risk: (cell.total_risk / cell.count).toFixed(2),
    intensity: cell.count
  }));
  
  res.json({
    success: true,
    period: `${hoursNum}h`,
    grid_size: gridSize,
    cells: heatmapArray.length,
    heatmap: heatmapArray
  });
}));

/**
 * GET /api/analytics/trends
 * Get trend analysis
 */
router.get('/trends', asyncHandler(async (req, res) => {
  const { days = 7 } = req.query;
  const daysNum = parseInt(days);
  
  const startDate = new Date(Date.now() - daysNum * 24 * 60 * 60 * 1000);
  
  const dailyTrends = await Event.aggregate([
    {
      $match: { timestamp: { $gte: startDate } }
    },
    {
      $group: {
        _id: {
          $dateToString: {
            format: '%Y-%m-%d',
            date: '$timestamp'
          }
        },
        count: { $sum: 1 },
        avg_risk: { $avg: '$risk_score' },
        high_risk_count: {
          $sum: {
            $cond: [{ $gte: ['$risk_score', 7] }, 1, 0]
          }
        }
      }
    },
    {
      $sort: { _id: 1 }
    },
    {
      $project: {
        date: '$_id',
        count: 1,
        avg_risk: { $round: ['$avg_risk', 2] },
        high_risk_count: 1,
        _id: 0
      }
    }
  ]);
  
  // Calculate trend direction
  let trend = 'stable';
  if (dailyTrends.length >= 2) {
    const recent = dailyTrends.slice(-3).reduce((sum, d) => sum + d.count, 0) / 3;
    const older = dailyTrends.slice(0, 3).reduce((sum, d) => sum + d.count, 0) / 3;
    
    if (recent > older * 1.2) trend = 'increasing';
    else if (recent < older * 0.8) trend = 'decreasing';
  }
  
  res.json({
    success: true,
    period: `${daysNum}d`,
    trend,
    daily_data: dailyTrends
  });
}));

/**
 * GET /api/analytics/zones
 * Get zone-specific analytics
 */
router.get('/zones', asyncHandler(async (req, res) => {
  const { hours = 24 } = req.query;
  const hoursNum = parseInt(hours);
  
  const startDate = new Date(Date.now() - hoursNum * 60 * 60 * 1000);
  
  const zoneStats = await Event.aggregate([
    {
      $match: { 
        timestamp: { $gte: startDate },
        'details.zone_id': { $exists: true }
      }
    },
    {
      $group: {
        _id: {
          zone_id: '$details.zone_id',
          zone_name: '$details.zone_name'
        },
        intrusions: { $sum: 1 },
        avg_risk: { $avg: '$risk_score' },
        max_risk: { $max: '$risk_score' }
      }
    },
    {
      $sort: { intrusions: -1 }
    },
    {
      $project: {
        zone_id: '$_id.zone_id',
        zone_name: '$_id.zone_name',
        intrusions: 1,
        avg_risk: { $round: ['$avg_risk', 2] },
        max_risk: 1,
        _id: 0
      }
    }
  ]);
  
  res.json({
    success: true,
    period: `${hoursNum}h`,
    zones: zoneStats
  });
}));

/**
 * GET /api/analytics/alerts
 * Get alert statistics
 */
router.get('/alerts', asyncHandler(async (req, res) => {
  const [
    totalAlerts,
    unreadAlerts,
    dismissedAlerts,
    alertsByPriority,
    avgResponseTime
  ] = await Promise.all([
    Alert.countDocuments(),
    Alert.countDocuments({ read: false }),
    Alert.countDocuments({ dismissed: true }),
    Alert.aggregate([
      { $group: { _id: '$priority', count: { $sum: 1 } } }
    ]),
    Alert.aggregate([
      {
        $match: { 
          read: true,
          read_at: { $exists: true }
        }
      },
      {
        $project: {
          response_time: {
            $subtract: ['$read_at', '$createdAt']
          }
        }
      },
      {
        $group: {
          _id: null,
          avg_response_ms: { $avg: '$response_time' }
        }
      }
    ])
  ]);
  
  const priorityMap = {};
  alertsByPriority.forEach(item => {
    priorityMap[item._id] = item.count;
  });
  
  res.json({
    success: true,
    summary: {
      total_alerts: totalAlerts,
      unread_alerts: unreadAlerts,
      dismissed_alerts: dismissedAlerts,
      avg_response_time_seconds: avgResponseTime[0] 
        ? Math.round(avgResponseTime[0].avg_response_ms / 1000) 
        : 0
    },
    alerts_by_priority: {
      LOW: priorityMap.LOW || 0,
      MEDIUM: priorityMap.MEDIUM || 0,
      HIGH: priorityMap.HIGH || 0,
      CRITICAL: priorityMap.CRITICAL || 0
    }
  });
}));

module.exports = router;