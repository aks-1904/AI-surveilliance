import React, { useState, useEffect } from "react";
import { useSocket } from "../hooks/useSocket";
import VideoPlayer from "../components/VideoPlayer";
import ZoneDrawer from "../components/ZoneDrawer";
import AlertPanel from "../components/AlertPanel";
import RiskIndicator from "../components/RiskIndicator";
import StatsCard from "../components/StatsCard";
import {
  startCamera,
  stopCamera,
  getAnalytics,
  resetAISystem,
} from "../services/api";
import FootageUploader from "../components/FootageUploader";
import LiveCameraFeed from "../components/LiveCameraFeed";

const Dashboard = () => {
  const { connected, alerts } = useSocket();
  const [cameraActive, setCameraActive] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [showZoneDrawer, setShowZoneDrawer] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAnalytics();
    const interval = setInterval(loadAnalytics, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadAnalytics = async () => {
    try {
      const data = await getAnalytics(24);
      setAnalytics(data);
    } catch (error) {
      console.error("Failed to load analytics:", error);
    }
  };

  const handleStartCamera = async () => {
    setLoading(true);
    try {
      await startCamera();
      setCameraActive(true);
    } catch (error) {
      console.error("Failed to start camera:", error);
      alert("Failed to start camera. Make sure AI service is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleStopCamera = async () => {
    setLoading(true);
    try {
      await stopCamera();
      setCameraActive(false);
    } catch (error) {
      console.error("Failed to stop camera:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetAISystem();
      alert("System trackers and statistics have been reset successfully.");
    } catch (error) {
      console.error("Failed to reset system:", error);
      alert("Failed to reset system.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                🎥 YU-WATCH 
                <br />
                <span className="text-lg text-gray-600">AI Surveillance Co-Pilot</span>
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Real-time security monitoring system
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div
                className={`flex items-center px-3 py-1 rounded-full ${connected ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}
              >
                <div
                  className={`w-2 h-2 rounded-full mr-2 ${connected ? "bg-green-600 animate-pulse" : "bg-red-600"}`}
                />
                <span className="text-sm font-medium">
                  {connected ? "Connected" : "Disconnected"}
                </span>
              </div>
              <button
                onClick={handleReset}
                className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
              >
                Reset System Trackers
              </button>
              <button
                onClick={cameraActive ? handleStopCamera : handleStartCamera}
                disabled={loading}
                className={`px-6 py-2 rounded-lg font-medium transition-all ${
                  cameraActive
                    ? "bg-red-600 hover:bg-red-700 text-white"
                    : "bg-green-600 hover:bg-green-700 text-white"
                } disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg`}
              >
                {loading
                  ? "⏳ Loading..."
                  : cameraActive
                    ? "⏹️ Stop Camera"
                    : "▶️ Start Camera"}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatsCard
            title="Total Events (24h)"
            value={analytics?.summary?.total_events || 0}
            icon="📊"
            color="blue"
          />
          <StatsCard
            title="Avg Risk Score"
            value={analytics?.summary?.average_risk_score || "0.0"}
            icon="⚠️"
            color="orange"
          />
          <StatsCard
            title="Active Alerts"
            value={alerts.length}
            icon="🔔"
            color="red"
          />
          <RiskIndicator alerts={alerts} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-gray-900">
                  📹 Live Feed
                </h2>
                <button
                  onClick={() => setShowZoneDrawer(!showZoneDrawer)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors shadow-sm"
                >
                  {showZoneDrawer ? "📹 Show Video" : "✏️ Draw Zone"}
                </button>
              </div>
              {showZoneDrawer ? (
                <ZoneDrawer
                  onZoneCreated={() => {
                    setShowZoneDrawer(false);
                    alert("Zone created successfully!");
                  }}
                />
              ) : (
                <VideoPlayer active={cameraActive} />
              )}
            </div>
          </div>

          <div className="lg:col-span-1">
            <AlertPanel alerts={alerts} onAlertAction={loadAnalytics} />
          </div>
        </div>

        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">
            📈 Event Statistics (24h)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                Events by Type
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm">🚫 Restricted Entry</span>
                  <span className="font-bold">
                    {analytics?.events_by_type?.RESTRICTED_ENTRY || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">⏱️ Loitering</span>
                  <span className="font-bold">
                    {analytics?.events_by_type?.LOITERING || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">💼 Unattended Object</span>
                  <span className="font-bold">
                    {analytics?.events_by_type?.UNATTENDED_OBJECT || 0}
                  </span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                Risk Distribution
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-red-600">● High</span>
                  <span className="font-bold">
                    {analytics?.risk_distribution?.HIGH || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-orange-600">● Medium</span>
                  <span className="font-bold">
                    {analytics?.risk_distribution?.MEDIUM || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-green-600">● Low</span>
                  <span className="font-bold">
                    {analytics?.risk_distribution?.LOW || 0}
                  </span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                System Status
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Active Zones</span>
                  <span className="font-bold">
                    {analytics?.summary?.active_zones || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Unread Alerts</span>
                  <span className="font-bold text-red-600">
                    {analytics?.summary?.unread_alerts || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Camera Status</span>
                  <span
                    className={`font-bold ${cameraActive ? "text-green-600" : "text-gray-400"}`}
                  >
                    {cameraActive ? "Active" : "Inactive"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-5">
          <FootageUploader />
        </div>
        <div className="mt-5">
          <LiveCameraFeed />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
