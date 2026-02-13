const express = require('express');
const router = express.Router();
const Zone = require('../models/Zone');
const { validateZone } = require('../middleware/validation');
const { asyncHandler } = require('../middleware/errorHandler');
const axios = require('axios');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:5000';

/**
 * POST /api/zones
 * Create a new restricted zone
 */
router.post('/', validateZone, asyncHandler(async (req, res) => {
  const { name, polygon, description, color, risk_multiplier, created_by } = req.body;
  
  // Check if zone name already exists
  const existingZone = await Zone.findOne({ name, active: true });
  if (existingZone) {
    return res.status(409).json({
      success: false,
      error: 'Zone with this name already exists',
      existing_zone_id: existingZone._id
    });
  }
  
  // Create zone in database
  const zone = new Zone({
    name,
    polygon,
    description,
    color: color || '#FF0000',
    risk_multiplier: risk_multiplier || 1.0,
    created_by: created_by || 'system',
    active: true
  });
  
  await zone.save();
  
  // Send to AI service
  try {
    await axios.post(`${AI_SERVICE_URL}/zones`, {
      zone_id: zone._id.toString(),
      name: zone.name,
      polygon: zone.polygon
    }, {
      timeout: 5000
    });
    
    console.log(`[ZONE CREATED] ${zone.name} - Synced with AI service`);
  } catch (aiError) {
    console.error('[ZONE SYNC ERROR] Failed to send zone to AI service:', aiError.message);
    // Don't fail the request if AI service is down
    // Zone is still saved in DB and can be synced later
  }
  
  // Broadcast zone creation
  const io = req.app.get('io');
  if (io) {
    io.emit('zone_created', zone);
  }
  
  res.status(201).json({
    success: true,
    zone,
    message: 'Zone created successfully'
  });
}));

/**
 * GET /api/zones
 * Get all zones (optionally filter by active status)
 */
router.get('/', asyncHandler(async (req, res) => {
  const { active } = req.query;
  
  const query = {};
  if (active !== undefined) {
    query.active = active === 'true';
  }
  
  const zones = await Zone.find(query).sort({ createdAt: -1 });
  
  res.json({
    success: true,
    zones,
    total: zones.length
  });
}));

/**
 * GET /api/zones/:id
 * Get a single zone by ID
 */
router.get('/:id', asyncHandler(async (req, res) => {
  const zone = await Zone.findById(req.params.id);
  
  if (!zone) {
    return res.status(404).json({
      success: false,
      error: 'Zone not found',
      zone_id: req.params.id
    });
  }
  
  res.json({
    success: true,
    zone
  });
}));

/**
 * PUT /api/zones/:id
 * Update a zone
 */
router.put('/:id', asyncHandler(async (req, res) => {
  const { name, polygon, description, color, risk_multiplier, active } = req.body;
  
  const zone = await Zone.findById(req.params.id);
  
  if (!zone) {
    return res.status(404).json({
      success: false,
      error: 'Zone not found',
      zone_id: req.params.id
    });
  }
  
  // Update fields
  if (name !== undefined) zone.name = name;
  if (polygon !== undefined) zone.polygon = polygon;
  if (description !== undefined) zone.description = description;
  if (color !== undefined) zone.color = color;
  if (risk_multiplier !== undefined) zone.risk_multiplier = risk_multiplier;
  if (active !== undefined) zone.active = active;
  
  await zone.save();
  
  // Sync with AI service
  try {
    if (zone.active) {
      await axios.put(`${AI_SERVICE_URL}/zones/${req.params.id}`, {
        name: zone.name,
        polygon: zone.polygon
      }, {
        timeout: 5000
      });
    } else {
      await axios.delete(`${AI_SERVICE_URL}/zones/${req.params.id}`, {
        timeout: 5000
      });
    }
    
    console.log(`[ZONE UPDATED] ${zone.name} - Synced with AI service`);
  } catch (aiError) {
    console.error('[ZONE SYNC ERROR] Failed to update zone in AI service:', aiError.message);
  }
  
  // Broadcast update
  const io = req.app.get('io');
  if (io) {
    io.emit('zone_updated', zone);
  }
  
  res.json({
    success: true,
    zone,
    message: 'Zone updated successfully'
  });
}));

/**
 * DELETE /api/zones/:id
 * Delete (deactivate) a zone
 */
router.delete('/:id', asyncHandler(async (req, res) => {
  const zone = await Zone.findById(req.params.id);
  
  if (!zone) {
    return res.status(404).json({
      success: false,
      error: 'Zone not found',
      zone_id: req.params.id
    });
  }
  
  // Soft delete by deactivating
  await zone.deactivate();
  
  // Notify AI service
  try {
    await axios.delete(`${AI_SERVICE_URL}/zones/${req.params.id}`, {
      timeout: 5000
    });
    
    console.log(`[ZONE DELETED] ${zone.name} - Removed from AI service`);
  } catch (aiError) {
    console.error('[ZONE SYNC ERROR] Failed to delete zone from AI service:', aiError.message);
  }
  
  // Broadcast deletion
  const io = req.app.get('io');
  if (io) {
    io.emit('zone_deleted', { zone_id: zone._id });
  }
  
  res.json({
    success: true,
    message: 'Zone deleted successfully',
    zone_id: zone._id
  });
}));

/**
 * POST /api/zones/sync
 * Sync all active zones with AI service
 */
router.post('/sync', asyncHandler(async (req, res) => {
  const activeZones = await Zone.getActiveZones();
  
  const syncResults = {
    success: [],
    failed: []
  };
  
  for (const zone of activeZones) {
    try {
      await axios.post(`${AI_SERVICE_URL}/zones`, {
        zone_id: zone._id.toString(),
        name: zone.name,
        polygon: zone.polygon
      }, {
        timeout: 5000
      });
      
      syncResults.success.push(zone._id);
    } catch (error) {
      syncResults.failed.push({
        zone_id: zone._id,
        error: error.message
      });
    }
  }
  
  console.log(`[ZONE SYNC] Synced ${syncResults.success.length}/${activeZones.length} zones`);
  
  res.json({
    success: true,
    synced: syncResults.success.length,
    failed: syncResults.failed.length,
    details: syncResults
  });
}));

module.exports = router;