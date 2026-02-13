import React from 'react';
import { acknowledgeEvent, markAlertAsRead } from '../services/api';

const AlertPanel = ({ alerts, onAlertAction }) => {
  const getRiskColor = (level) => {
    switch (level) {
      case 'HIGH':
      case 'CRITICAL':
        return 'bg-red-50 border-red-500 text-red-900';
      case 'MEDIUM':
        return 'bg-orange-50 border-orange-500 text-orange-900';
      case 'LOW':
        return 'bg-green-50 border-green-500 text-green-900';
      default:
        return 'bg-gray-50 border-gray-500 text-gray-900';
    }
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'RESTRICTED_ENTRY':
        return '🚫';
      case 'LOITERING':
        return '⏱️';
      case 'UNATTENDED_OBJECT':
        return '💼';
      default:
        return '⚠️';
    }
  };

  const handleAcknowledge = async (alert) => {
    try {
      await acknowledgeEvent(alert.event._id);
      await markAlertAsRead(alert.alert._id);
      if (onAlertAction) onAlertAction();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">🔔 Recent Alerts</h2>
        <span className="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded-full">
          {alerts.length}
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <svg className="w-16 h-16 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-center font-medium">No alerts</p>
            <p className="text-sm text-center mt-1">All clear!</p>
          </div>
        ) : (
          alerts.map((alert, index) => (
            <div
              key={index}
              className={`p-3 border-l-4 rounded-r-lg shadow-sm transition-all hover:shadow-md ${getRiskColor(alert.event.risk_level)}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2 flex-1">
                  <span className="text-2xl flex-shrink-0">{getEventIcon(alert.event.event_type)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm truncate">
                      {alert.event.event_type.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs mt-1 line-clamp-2">
                      {alert.event.details?.message || alert.alert.message}
                    </p>
                    <div className="flex items-center gap-2 mt-2 text-xs">
                      <span className="text-gray-600">
                        {formatTime(alert.event.timestamp)}
                      </span>
                      <span className={`font-bold px-2 py-0.5 rounded ${
                        alert.event.risk_level === 'HIGH' || alert.event.risk_level === 'CRITICAL'
                          ? 'bg-red-600 text-white'
                          : alert.event.risk_level === 'MEDIUM'
                          ? 'bg-orange-600 text-white'
                          : 'bg-green-600 text-white'
                      }`}>
                        {alert.event.risk_level}
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleAcknowledge(alert)}
                  className="flex-shrink-0 px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                  title="Acknowledge"
                >
                  ✓
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AlertPanel;