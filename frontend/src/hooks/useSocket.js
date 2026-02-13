import { useEffect, useState, useCallback } from 'react';
import { socket, connectSocket, disconnectSocket, setupSocketListeners, removeSocketListeners } from '../services/socket';

export const useSocket = () => {
  const [connected, setConnected] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [connectionError, setConnectionError] = useState(null);

  const handleConnect = useCallback(() => {
    setConnected(true);
    setConnectionError(null);
  }, []);

  const handleDisconnect = useCallback((reason) => {
    setConnected(false);
    if (reason === 'io server disconnect') {
      // Server disconnected, try to reconnect
      setTimeout(() => {
        connectSocket();
      }, 1000);
    }
  }, []);

  const handleError = useCallback((error) => {
    setConnectionError(error.message || 'Connection error');
  }, []);

  const handleAlert = useCallback((data) => {
    setAlerts(prev => {
      // Add new alert to the beginning
      const newAlerts = [data, ...prev];
      // Keep only last 100 alerts
      return newAlerts.slice(0, 100);
    });

    // Play notification sound or show browser notification
    if (Notification.permission === 'granted') {
      new Notification('New Security Alert', {
        body: data.alert?.message || 'A new event has been detected',
        icon: '/alert-icon.png',
        badge: '/badge-icon.png'
      });
    }
  }, []);

  const handleStatsUpdate = useCallback((data) => {
    setStats(data);
  }, []);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  const removeAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(alert => alert.alert?._id !== alertId));
  }, []);

  useEffect(() => {
    // Setup socket listeners
    setupSocketListeners({
      onConnect: handleConnect,
      onDisconnect: handleDisconnect,
      onError: handleError,
      onAlert: handleAlert,
      onStatsUpdate: handleStatsUpdate
    });

    // Connect socket
    connectSocket();

    // Request notification permission
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Cleanup
    return () => {
      removeSocketListeners();
      disconnectSocket();
    };
  }, [handleConnect, handleDisconnect, handleError, handleAlert, handleStatsUpdate]);

  return {
    connected,
    alerts,
    stats,
    connectionError,
    clearAlerts,
    removeAlert,
    socket
  };
};

export default useSocket;