import React from 'react';

const LiveCameraFeed = () => {
  // Use the AI service base URL
  const AI_BASE = process.env.REACT_APP_AI_SERVICE_URL || 'http://localhost:5000';
  const videoStreamUrl = `${AI_BASE}/video_feed`;

  return (
    <div className="border-4 border-gray-800 rounded overflow-hidden">
      <h2 className="bg-gray-800 text-white p-2 m-0 text-center">Live Surveillance Feed</h2>
      
      {/* The browser natively handles the multipart stream via the img tag */}
      <img 
        src={videoStreamUrl} 
        alt="AI Camera Feed" 
        className="w-full h-auto block"
        onError={(e) => {
          e.target.onerror = null; 
          e.target.src = '/path/to/fallback-image-or-offline-message.png';
        }}
      />
    </div>
  );
};

export default LiveCameraFeed;