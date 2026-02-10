# API Documentation

## Overview

The AI Video Processing Service provides a RESTful API for managing video surveillance with real-time AI analysis.

**Base URL**: `http://localhost:8000`

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "processor_running": true
}
```

---

### 2. Start Video Processing

**POST** `/start`

Start processing a video source (RTSP stream or file path).

**Request Body:**
```json
{
  "source": "rtsp://username:password@192.168.1.100:554/stream1",
  "source_type": "rtsp"  // optional: "rtsp" or "file", auto-detected if omitted
}
```

**Response:**
```json
{
  "status": "started",
  "source": "rtsp://username:password@192.168.1.100:554/stream1",
  "source_type": "rtsp"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d '{
    "source": "rtsp://admin:password@192.168.1.100:554/stream1",
    "source_type": "rtsp"
  }'
```

---

### 3. Upload Video File

**POST** `/upload`

Upload and immediately start processing a video file.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` (video file)

**Response:**
```json
{
  "status": "uploaded and processing",
  "filename": "surveillance_footage.mp4",
  "filepath": "/path/to/uploads/surveillance_footage.mp4"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/video.mp4"
```

---

### 4. Video Stream

**GET** `/video`

Get live MJPEG video stream with AI annotations.

**Response:**
- Content-Type: `multipart/x-mixed-replace; boundary=frame`
- MJPEG stream

**Usage in HTML:**
```html
<img src="http://localhost:8000/video" width="100%" />
```

**Usage in React:**
```jsx
<img 
  src="http://localhost:8000/video" 
  alt="Live surveillance feed"
  style={{ width: '100%' }}
/>
```

---

### 5. Get Statistics

**GET** `/stats`

Get current processing statistics.

**Response:**
```json
{
  "total_frames": 15000,
  "processed_frames": 15000,
  "detections": 4500,
  "events": 23,
  "fps": 28.5,
  "processing_time": 0.035,
  "running": true,
  "source": "rtsp://192.168.1.100:554/stream1"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/stats
```

---

### 6. Stop Processing

**POST** `/stop`

Stop current video processing.

**Response:**
```json
{
  "status": "stopped"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/stop
```

---

### 7. Get Configuration

**GET** `/config`

Get current system configuration.

**Response:**
```json
{
  "confidence_threshold": 0.5,
  "classes": ["person", "backpack", "handbag", "suitcase", "car", "motorcycle"],
  "loitering_threshold": 300,
  "crowd_threshold": 10,
  "face_blur_enabled": true,
  "tracking_enabled": true
}
```

**cURL Example:**
```bash
curl http://localhost:8000/config
```

---

## Event Webhook

The service automatically sends detected events to your backend API endpoint configured in `config.py`.

**POST** `{BACKEND_EVENT_ENDPOINT}`

**Payload Example:**
```json
{
  "type": "restricted_zone",
  "object_id": 5,
  "object_class": "person",
  "bbox": [100, 200, 300, 500],
  "zone_id": 0,
  "risk": 8,
  "timestamp": 1709231456.789,
  "description": "Person detected in restricted zone 0",
  "camera_id": "camera_001",
  "source": "rtsp://192.168.1.100:554/stream1"
}
```

---

## Event Types Reference

### Restricted Zone Violation

```json
{
  "type": "restricted_zone",
  "object_id": 5,
  "object_class": "person",
  "bbox": [100, 200, 300, 500],
  "zone_id": 0,
  "risk": 8,
  "timestamp": 1709231456.789,
  "description": "Person detected in restricted zone 0"
}
```

### Loitering Detection

```json
{
  "type": "loitering",
  "object_id": 3,
  "object_class": "person",
  "bbox": [150, 250, 350, 550],
  "duration": 320.5,
  "risk": 6,
  "timestamp": 1709231456.789,
  "description": "Person loitering for 320 seconds"
}
```

### Unattended Object

```json
{
  "type": "unattended_object",
  "object_id": 12,
  "object_class": "backpack",
  "bbox": [200, 300, 280, 400],
  "duration": 45.2,
  "risk": 7,
  "timestamp": 1709231456.789,
  "description": "Unattended backpack for 45 seconds"
}
```

### Crowd Detection

```json
{
  "type": "crowd_spike",
  "person_count": 25,
  "previous_avg": 12.5,
  "risk": 5,
  "timestamp": 1709231456.789,
  "description": "Sudden crowd increase: 25 people"
}
```

---

## Error Responses

All endpoints may return error responses:

**400 Bad Request**
```json
{
  "error": "Source is required"
}
```

**404 Not Found**
```json
{
  "error": "No processor active"
}
```

**500 Internal Server Error**
```json
{
  "error": "Error message details"
}
```

---

## Integration Examples

### JavaScript (Frontend)

```javascript
// Start RTSP stream
async function startCamera() {
  const response = await fetch('http://localhost:8000/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source: 'rtsp://192.168.1.100:554/stream1',
      source_type: 'rtsp'
    })
  });
  
  const data = await response.json();
  console.log('Camera started:', data);
}

// Get live stats
async function getStats() {
  const response = await fetch('http://localhost:8000/stats');
  const stats = await response.json();
  console.log('Stats:', stats);
}

// Upload video file
async function uploadVideo(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/upload', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  console.log('Upload result:', data);
}
```

### Node.js (Backend)

```javascript
const express = require('express');
const app = express();

// Receive events from AI service
app.post('/api/events', async (req, res) => {
  const event = req.body;
  
  console.log('Event received:', event.type);
  
  // Save to database
  await Event.create(event);
  
  // Emit to frontend via Socket.IO
  io.emit('event', event);
  
  res.json({ success: true });
});

app.listen(5000);
```

### Python

```python
import requests

# Start processing
response = requests.post('http://localhost:8000/start', json={
    'source': 'rtsp://camera-url',
    'source_type': 'rtsp'
})
print(response.json())

# Get stats
stats = requests.get('http://localhost:8000/stats').json()
print(f"FPS: {stats['fps']}, Events: {stats['events']}")

# Stop processing
requests.post('http://localhost:8000/stop')
```

---

## WebSocket Support (Optional)

For real-time event streaming, you can modify `app.py` to add Socket.IO support:

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

def send_event_websocket(event):
    socketio.emit('event', event)

processor.set_event_callback(send_event_websocket)

if __name__ == '__main__':
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT)
```

Then in frontend:

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8000');

socket.on('event', (event) => {
  console.log('Real-time event:', event);
  // Update UI
});
```

---

## Rate Limiting

Currently, the API has no rate limiting. For production:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/start', methods=['POST'])
@limiter.limit("10 per minute")
def start_processing():
    # ...
```

---

## Authentication

For production, add authentication:

```python
from functools import wraps
from flask import request

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/start', methods=['POST'])
@require_api_key
def start_processing():
    # ...
```

Usage:
```bash
curl -X POST http://localhost:8000/start \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"source": "rtsp://camera-url"}'
```