import React, { useState } from "react";
import {
  acknowledgeEvent,
  markAlertAsRead,
  sendGuardMessage,
} from "../services/api";

const AlertPanel = ({ alerts, onAlertAction }) => {
  const [replyText, setReplyText] = useState({});
  const [hiddenAlerts, setHiddenAlerts] = useState(new Set());

  const getRiskColor = (level) => {
    switch (level) {
      case "HIGH":
      case "CRITICAL":
        return "bg-red-50 border-red-500 text-red-900";
      case "MEDIUM":
        return "bg-orange-50 border-orange-500 text-orange-900";
      case "LOW":
        return "bg-green-50 border-green-500 text-green-900";
      default:
        return "bg-gray-50 border-gray-500 text-gray-900";
    }
  };

  const handleAcknowledge = async (currentAlert) => {
    // Safely extract IDs depending on how your Mongoose aggregation returns them
    const eventId = currentAlert.event?._id || currentAlert.eventId;
    const alertId = currentAlert.alert?._id || currentAlert._id;

    if (!eventId || !alertId) {
      console.error("Missing ID! Cannot clear.", {
        eventId,
        alertId,
        currentAlert,
      });
      return;
    }

    setHiddenAlerts((prev) => new Set(prev).add(alertId));

    try {
      // 1. Call your APIs

      await acknowledgeEvent(eventId);
      await markAlertAsRead(alertId);

      // 2. Trigger the parent to re-fetch the data
      if (onAlertAction) {
        onAlertAction();
      } else {
        console.warn(
          "The 'onAlertAction' prop is missing in AlertPanel. The DB updated, but the UI won't refresh automatically.",
        );
      }
    } catch (error) {
      console.error("Failed to clear alert:", error);
      setHiddenAlerts((prev) => {
        const newSet = new Set(prev);
        newSet.delete(alertId);
        return newSet;
      });
    }
  };

  const handleSendMessage = async (alertId) => {
    const text = replyText[alertId];
    if (!text || text.trim() === "") return;

    try {
      // Assuming 'Guard 1' is logged in. In a real app, get this from Auth context.
      await sendGuardMessage(alertId, "Admin", text);

      // Clear input
      setReplyText((prev) => ({ ...prev, [alertId]: "" }));
      if (onAlertAction) onAlertAction(); // Refresh data
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString();
  };

  const visibleALerts = alerts.filter((a) => {
    const id = a.alert?._id || a._id;
    return !hiddenAlerts.has(id);
  });

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">
          🔔 Active Alerts & Dispatch
        </h2>
        <span className="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded-full">
          {visibleALerts.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {visibleALerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <p className="font-medium">No active alerts</p>
          </div>
        ) : (
          visibleALerts.map((alert, index) => (
            <div
              key={index}
              className={`p-3 border-l-4 rounded-r-lg shadow-sm ${getRiskColor(alert.event.risk_level)}`}
            >
              {/* Alert Header */}
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-bold text-sm">
                    {alert.event.event_type.replace(/_/g, " ")}
                  </p>
                  <p className="text-xs font-medium text-gray-700">
                    📍 Camera 1 (Main Gate) • Assigned:{" "}
                    {alert.alert?.assigned_guard || "Auto-Dispatch"}
                  </p>
                </div>
                <span className="text-xs font-bold px-2 py-1 bg-white/50 rounded">
                  {formatTime(alert.event.timestamp)}
                </span>
              </div>

              {/* Threat Intelligence / Biometrics */}
              {alert.event.attributes && (
                <div className="bg-white/60 p-2 rounded text-xs mb-3">
                  <p className="font-bold mb-1">🔍 Suspect Details:</p>
                  <ul className="list-disc list-inside text-gray-800">
                    {alert.event.attributes.upper_clothing_color && (
                      <li>
                        Wearing: {alert.event.attributes.upper_clothing_color}{" "}
                        top
                      </li>
                    )}
                    {alert.event.attributes.body_type && (
                      <li>Build: {alert.event.attributes.body_type}</li>
                    )}
                  </ul>
                </div>
              )}

              {/* Guard Communication Log */}
              <div className="bg-gray-50 rounded p-2 mb-3 max-h-32 overflow-y-auto">
                <p className="text-[10px] uppercase font-bold text-gray-400 mb-1">
                  Communication Log
                </p>
                <div className="text-xs text-gray-800 mb-1">
                  <span className="font-bold text-blue-600">System:</span>{" "}
                  Suspect detected in restricted zone. Proceed with caution.
                </div>
                {alert.alert.guard_notes?.map((note, i) => (
                  <div key={i} className="text-xs text-gray-800 mb-1">
                    <span
                      className={`font-bold ${note.sender === "System" ? "text-blue-600" : "text-green-600"}`}
                    >
                      {note.sender}:
                    </span>{" "}
                    {note.message}
                  </div>
                ))}
              </div>

              {/* Action Bar */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Type update (e.g., 'Checking area now')"
                  className="flex-1 text-xs p-1.5 rounded border border-gray-300"
                  value={replyText[alert.alert._id] || ""}
                  onChange={(e) =>
                    setReplyText({
                      ...replyText,
                      [alert.alert._id]: e.target.value,
                    })
                  }
                  onKeyPress={(e) =>
                    e.key === "Enter" && handleSendMessage(alert.alert._id)
                  }
                />
                <button
                  onClick={() => handleSendMessage(alert.alert._id)}
                  className="px-3 py-1.5 bg-gray-800 text-white text-xs rounded hover:bg-gray-700"
                >
                  Send
                </button>
                <button
                  onClick={() => handleAcknowledge(alert)}
                  className="px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                  title="Mark Safe & Close"
                >
                  Clear
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
