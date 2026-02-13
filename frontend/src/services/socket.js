import { io } from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_WS_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:3000';

// Create socket instance
export const socket = io(SOCKET_URL, {
  autoConnect: false,
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 10,
  timeout: 10000
});

// Connection management
export const connectSocket = () => {
  if (!socket.connected) {
    console.log('[Socket] Connecting to:', SOCKET_URL);
    socket.connect();
  }
};

export const disconnectSocket = () => {
  if (socket.connected) {
    console.log('[Socket] Disconnecting');
    socket.disconnect();
  }
};

// Event listeners setup
export const setupSocketListeners = (callbacks = {}) => {
  // Connection events
  socket.on('connect', () => {
    console.log('[Socket] Connected:', socket.id);
    if (callbacks.onConnect) callbacks.onConnect();
  });

  socket.on('disconnect', (reason) => {
    console.log('[Socket] Disconnected:', reason);
    if (callbacks.onDisconnect) callbacks.onDisconnect(reason);
  });

  socket.on('connect_error', (error) => {
    console.error('[Socket] Connection error:', error);
    if (callbacks.onError) callbacks.onError(error);
  });

  socket.on('error', (error) => {
    console.error('[Socket] Error:', error);
    if (callbacks.onError) callbacks.onError(error);
  });

  // Custom events
  socket.on('alert', (data) => {
    console.log('[Socket] Alert received:', data);
    if (callbacks.onAlert) callbacks.onAlert(data);
  });

  socket.on('stats_update', (data) => {
    console.log('[Socket] Stats update:', data);
    if (callbacks.onStatsUpdate) callbacks.onStatsUpdate(data);
  });

  socket.on('zone_created', (data) => {
    console.log('[Socket] Zone created:', data);
    if (callbacks.onZoneCreated) callbacks.onZoneCreated(data);
  });

  socket.on('zone_updated', (data) => {
    console.log('[Socket] Zone updated:', data);
    if (callbacks.onZoneUpdated) callbacks.onZoneUpdated(data);
  });

  socket.on('zone_deleted', (data) => {
    console.log('[Socket] Zone deleted:', data);
    if (callbacks.onZoneDeleted) callbacks.onZoneDeleted(data);
  });

  socket.on('event_acknowledged', (data) => {
    console.log('[Socket] Event acknowledged:', data);
    if (callbacks.onEventAcknowledged) callbacks.onEventAcknowledged(data);
  });

  socket.on('heartbeat', (data) => {
    if (process.env.REACT_APP_DEBUG === 'true') {
      console.log('[Socket] Heartbeat:', data);
    }
    if (callbacks.onHeartbeat) callbacks.onHeartbeat(data);
  });

  socket.on('client_count', (count) => {
    if (process.env.REACT_APP_DEBUG === 'true') {
      console.log('[Socket] Connected clients:', count);
    }
    if (callbacks.onClientCount) callbacks.onClientCount(count);
  });
};

// Remove all listeners
export const removeSocketListeners = () => {
  socket.off('connect');
  socket.off('disconnect');
  socket.off('connect_error');
  socket.off('error');
  socket.off('alert');
  socket.off('stats_update');
  socket.off('zone_created');
  socket.off('zone_updated');
  socket.off('zone_deleted');
  socket.off('event_acknowledged');
  socket.off('heartbeat');
  socket.off('client_count');
};

// Subscribe to specific channels
export const subscribe = (channel) => {
  socket.emit('subscribe', { channel });
};

// Unsubscribe from channels
export const unsubscribe = (channel) => {
  socket.emit('unsubscribe', { channel });
};

// Send ping for keepalive
export const sendPing = () => {
  socket.emit('ping');
};

export default socket;