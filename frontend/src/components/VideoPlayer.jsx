import React, { useState, useEffect } from 'react';

const VideoPlayer = ({ active }) => {
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const VIDEO_STREAM_URL = process.env.REACT_APP_VIDEO_STREAM_URL || 'http://localhost:5000/video_feed';

  useEffect(() => {
    if (active) {
      setLoading(false);
      setError(null);
      // Generate unique URL to prevent caching
      setImageUrl(`${VIDEO_STREAM_URL}?t=${Date.now()}`);
    } else {
      setImageUrl(null);
      setLoading(true);
    }
  }, [active, VIDEO_STREAM_URL]);

  const handleImageError = () => {
    setError('Failed to load video stream. Make sure the AI service is running.');
    setLoading(false);
  };

  const handleImageLoad = () => {
    setLoading(false);
    setError(null);
  };

  if (!active) {
    return (
      <div className="flex items-center justify-center bg-gray-900 rounded-lg" style={{ height: '480px' }}>
        <div className="text-center text-gray-400">
          <svg className="w-24 h-24 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <p className="text-lg font-medium">Camera Inactive</p>
          <p className="text-sm mt-2">Click "Start Camera" to begin monitoring</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative bg-gray-900 rounded-lg overflow-hidden" style={{ height: '480px' }}>
      {loading && !error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p>Loading video stream...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-red-400 px-4">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="font-medium">{error}</p>
            <button 
              onClick={() => {
                setError(null);
                setImageUrl(`${VIDEO_STREAM_URL}?t=${Date.now()}`);
              }}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {imageUrl && (
        <img 
          src={imageUrl}
          alt="Live video feed"
          className="w-full h-full object-contain"
          onError={handleImageError}
          onLoad={handleImageLoad}
          style={{ display: loading ? 'none' : 'block' }}
        />
      )}

      {/* Live indicator */}
      {active && !error && (
        <div className="absolute top-4 left-4 flex items-center bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
          <span className="animate-pulse mr-2">●</span>
          LIVE
        </div>
      )}

      {/* Timestamp overlay */}
      {active && !error && (
        <div className="absolute bottom-4 left-4 bg-black bg-opacity-70 text-white px-3 py-1 rounded text-xs font-mono">
          {new Date().toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;