import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:3000';
const AI_BASE = process.env.REACT_APP_AI_SERVICE_URL || 'http://localhost:5000';

// Create axios instance for backend
const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
});

// Create axios instance for AI service
const aiApi = axios.create({
  baseURL: AI_BASE,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('[API Error]', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ==================== EVENTS API ====================

export const getEvents = async (params = {}) => {
  try {
    const response = await api.get('/events', { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getEvent = async (eventId) => {
  try {
    const response = await api.get(`/events/${eventId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const acknowledgeEvent = async (eventId, user = 'user', notes = '') => {
  try {
    const response = await api.put(`/events/${eventId}/acknowledge`, { user, notes });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const deleteEvent = async (eventId) => {
  try {
    const response = await api.delete(`/events/${eventId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getEventStats = async () => {
  try {
    const response = await api.get('/events/stats/summary');
    return response.data;
  } catch (error) {
    throw error;
  }
};

// ==================== ZONES API ====================

export const getZones = async (activeOnly = true) => {
  try {
    const params = activeOnly ? { active: true } : {};
    const response = await api.get('/zones', { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getZone = async (zoneId) => {
  try {
    const response = await api.get(`/zones/${zoneId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const createZone = async (zoneData) => {
  try {
    const response = await api.post('/zones', zoneData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const updateZone = async (zoneId, zoneData) => {
  try {
    const response = await api.put(`/zones/${zoneId}`, zoneData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const deleteZone = async (zoneId) => {
  try {
    const response = await api.delete(`/zones/${zoneId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const syncZones = async () => {
  try {
    const response = await api.post('/zones/sync');
    return response.data;
  } catch (error) {
    throw error;
  }
};

// ==================== ANALYTICS API ====================

export const getAnalytics = async (hours = 24) => {
  try {
    const response = await api.get('/analytics/summary', { params: { hours } });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getTimeline = async (hours = 24) => {
  try {
    const response = await api.get('/analytics/timeline', { params: { hours } });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getHeatmap = async (hours = 24, gridSize = 50) => {
  try {
    const response = await api.get('/analytics/heatmap', { 
      params: { hours, grid_size: gridSize } 
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getTrends = async (days = 7) => {
  try {
    const response = await api.get('/analytics/trends', { params: { days } });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getZoneAnalytics = async (hours = 24) => {
  try {
    const response = await api.get('/analytics/zones', { params: { hours } });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAlertAnalytics = async () => {
  try {
    const response = await api.get('/analytics/alerts');
    return response.data;
  } catch (error) {
    throw error;
  }
};

// ==================== ALERTS API ====================

export const getAlerts = async (params = {}) => {
  try {
    const response = await api.get('/alerts', { params });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getUnreadAlerts = async () => {
  try {
    const response = await api.get('/alerts/unread');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const markAlertAsRead = async (alertId, user = 'user') => {
  try {
    const response = await api.put(`/alerts/${alertId}/read`, { user });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const dismissAlert = async (alertId, user = 'user', action = '') => {
  try {
    const response = await api.put(`/alerts/${alertId}/dismiss`, { user, action });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const markAllAlertsAsRead = async (user = 'user') => {
  try {
    const response = await api.post('/alerts/mark-all-read', { user });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// ==================== AI SERVICE API ====================

export const startCamera = async () => {
  try {
    const response = await aiApi.post('/start');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const stopCamera = async () => {
  try {
    const response = await aiApi.post('/stop');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAIStats = async () => {
  try {
    const response = await aiApi.get('/stats');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAIHealth = async () => {
  try {
    const response = await aiApi.get('/health');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getBackendHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export default api;