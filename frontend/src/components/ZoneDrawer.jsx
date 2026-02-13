import React, { useState } from 'react';
import { Stage, Layer, Line, Circle } from 'react-konva';
import { createZone } from '../services/api';

const ZoneDrawer = ({ onZoneCreated, videoWidth = 640, videoHeight = 480 }) => {
  const [points, setPoints] = useState([]);
  const [zoneName, setZoneName] = useState('');
  const [description, setDescription] = useState('');
  const [isDrawing, setIsDrawing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  const handleStageClick = (e) => {
    if (!isDrawing) return;

    const stage = e.target.getStage();
    const point = stage.getPointerPosition();
    
    setPoints([...points, { x: point.x, y: point.y }]);
  };

  const handleSaveZone = async () => {
    if (points.length < 3) {
      setError('Please draw at least 3 points to create a zone');
      return;
    }

    if (!zoneName.trim()) {
      setError('Please enter a zone name');
      return;
    }

    setCreating(true);
    setError(null);

    try {
      await createZone({
        name: zoneName,
        polygon: points,
        description: description || undefined
      });
      
      setPoints([]);
      setZoneName('');
      setDescription('');
      setIsDrawing(false);
      
      if (onZoneCreated) onZoneCreated();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create zone');
    } finally {
      setCreating(false);
    }
  };

  const handleClear = () => {
    setPoints([]);
    setError(null);
  };

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <input
          type="text"
          placeholder="Zone Name (e.g., Server Room)"
          value={zoneName}
          onChange={(e) => setZoneName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        
        {error && (
          <div className="px-3 py-2 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={() => setIsDrawing(!isDrawing)}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              isDrawing 
                ? 'bg-red-600 hover:bg-red-700 text-white' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isDrawing ? '⏸️ Stop Drawing' : '✏️ Start Drawing'}
          </button>
          <button
            onClick={handleClear}
            disabled={points.length === 0}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            🗑️ Clear
          </button>
          <button
            onClick={handleSaveZone}
            disabled={points.length < 3 || !zoneName.trim() || creating}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {creating ? '⏳ Saving...' : '💾 Save Zone'}
          </button>
        </div>
      </div>

      <Stage
        width={videoWidth}
        height={videoHeight}
        onClick={handleStageClick}
        className="border-2 border-gray-300 rounded-lg bg-gray-800 cursor-crosshair"
      >
        <Layer>
          {points.length > 0 && (
            <Line
              points={points.flatMap(p => [p.x, p.y])}
              stroke="#EF4444"
              strokeWidth={3}
              closed={points.length > 2}
              fill={points.length > 2 ? 'rgba(239, 68, 68, 0.2)' : undefined}
            />
          )}
          
          {points.map((point, i) => (
            <Circle
              key={i}
              x={point.x}
              y={point.y}
              radius={6}
              fill="#EF4444"
              stroke="#FFF"
              strokeWidth={2}
            />
          ))}
        </Layer>
      </Stage>

      <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg border border-blue-200">
        <p className="font-medium text-blue-900 mb-1">📍 Instructions:</p>
        <ul className="list-disc list-inside space-y-1 text-blue-800">
          <li>Click "Start Drawing" to enable zone creation</li>
          <li>Click on the canvas to add points (minimum 3 points)</li>
          <li>The zone will automatically close when you add the 3rd point</li>
          <li>Enter a name and click "Save Zone" when finished</li>
        </ul>
        <p className="mt-2 text-blue-700">
          <strong>Points drawn:</strong> {points.length} {points.length >= 3 ? '✅' : ''}
        </p>
      </div>
    </div>
  );
};

export default ZoneDrawer;