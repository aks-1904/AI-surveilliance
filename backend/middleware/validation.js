/**
 * Validation middleware for request data
 */

const validateEvent = (req, res, next) => {
  const { event_type, risk_score, risk_level } = req.body;
  
  // Check required fields
  if (!event_type) {
    return res.status(400).json({ 
      error: 'Missing required field: event_type',
      field: 'event_type'
    });
  }
  
  if (risk_score === undefined || risk_score === null) {
    return res.status(400).json({ 
      error: 'Missing required field: risk_score',
      field: 'risk_score'
    });
  }
  
  if (!risk_level) {
    return res.status(400).json({ 
      error: 'Missing required field: risk_level',
      field: 'risk_level'
    });
  }
  
  // Validate event_type
  const validEventTypes = ['RESTRICTED_ENTRY', 'LOITERING', 'UNATTENDED_OBJECT'];
  if (!validEventTypes.includes(event_type)) {
    return res.status(400).json({ 
      error: 'Invalid event_type. Must be one of: ' + validEventTypes.join(', '),
      field: 'event_type',
      received: event_type
    });
  }
  
  // Validate risk_score
  if (typeof risk_score !== 'number' || risk_score < 0 || risk_score > 10) {
    return res.status(400).json({ 
      error: 'Invalid risk_score. Must be a number between 0 and 10',
      field: 'risk_score',
      received: risk_score
    });
  }
  
  // Validate risk_level
  const validRiskLevels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
  if (!validRiskLevels.includes(risk_level)) {
    return res.status(400).json({ 
      error: 'Invalid risk_level. Must be one of: ' + validRiskLevels.join(', '),
      field: 'risk_level',
      received: risk_level
    });
  }
  
  next();
};

const validateZone = (req, res, next) => {
  const { name, polygon } = req.body;
  
  // Check required fields
  if (!name || !name.trim()) {
    return res.status(400).json({ 
      error: 'Missing or empty required field: name',
      field: 'name'
    });
  }
  
  if (!polygon || !Array.isArray(polygon)) {
    return res.status(400).json({ 
      error: 'Missing or invalid required field: polygon (must be an array)',
      field: 'polygon'
    });
  }
  
  // Validate polygon has at least 3 points
  if (polygon.length < 3) {
    return res.status(400).json({ 
      error: 'Polygon must have at least 3 points',
      field: 'polygon',
      received: polygon.length + ' points'
    });
  }
  
  // Validate each point has x and y coordinates
  for (let i = 0; i < polygon.length; i++) {
    const point = polygon[i];
    if (typeof point.x !== 'number' || typeof point.y !== 'number') {
      return res.status(400).json({ 
        error: `Invalid point at index ${i}. Each point must have numeric x and y coordinates`,
        field: 'polygon',
        point_index: i,
        received: point
      });
    }
  }
  
  next();
};

const validatePagination = (req, res, next) => {
  const { limit, offset } = req.query;
  
  if (limit) {
    const limitNum = parseInt(limit);
    if (isNaN(limitNum) || limitNum < 1 || limitNum > 1000) {
      return res.status(400).json({ 
        error: 'Invalid limit. Must be a number between 1 and 1000',
        field: 'limit',
        received: limit
      });
    }
  }
  
  if (offset) {
    const offsetNum = parseInt(offset);
    if (isNaN(offsetNum) || offsetNum < 0) {
      return res.status(400).json({ 
        error: 'Invalid offset. Must be a non-negative number',
        field: 'offset',
        received: offset
      });
    }
  }
  
  next();
};

const validateDateRange = (req, res, next) => {
  const { start_date, end_date } = req.query;
  
  if (start_date) {
    const startDate = new Date(start_date);
    if (isNaN(startDate.getTime())) {
      return res.status(400).json({ 
        error: 'Invalid start_date. Must be a valid ISO 8601 date',
        field: 'start_date',
        received: start_date
      });
    }
  }
  
  if (end_date) {
    const endDate = new Date(end_date);
    if (isNaN(endDate.getTime())) {
      return res.status(400).json({ 
        error: 'Invalid end_date. Must be a valid ISO 8601 date',
        field: 'end_date',
        received: end_date
      });
    }
  }
  
  if (start_date && end_date) {
    const start = new Date(start_date);
    const end = new Date(end_date);
    if (start > end) {
      return res.status(400).json({ 
        error: 'start_date must be before end_date',
        start_date: start_date,
        end_date: end_date
      });
    }
  }
  
  next();
};

module.exports = {
  validateEvent,
  validateZone,
  validatePagination,
  validateDateRange
};