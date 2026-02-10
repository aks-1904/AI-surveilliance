# AI Surveillance Co-Pilot - Project Overview

## 🎯 Project Vision

A production-ready AI-powered CCTV surveillance system that provides real-time intelligent monitoring with event detection, object tracking, and privacy protection.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VIDEO INPUT SOURCES                       │
├─────────────────────────────────────────────────────────────┤
│  RTSP Camera Stream  │  Uploaded Video Files  │  Local Files│
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   VIDEO PROCESSOR CORE                       │
├─────────────────────────────────────────────────────────────┤
│  • Frame Capture & Preprocessing                            │
│  • YOLOv8 Object Detection                                  │
│  • Object Tracking (Centroid-based)                         │
│  • Event Detection Engine                                   │
│  • Privacy Protection (Face Blur)                           │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                     FLASK API SERVER                         │
├─────────────────────────────────────────────────────────────┤
│  • REST API Endpoints                                       │
│  • MJPEG Video Streaming                                    │
│  • Event Webhooks                                           │
│  • Statistics & Monitoring                                  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND INTEGRATION                        │
├─────────────────────────────────────────────────────────────┤
│  Node.js + Express + MongoDB + Socket.IO                    │
│  • Event Storage                                            │
│  • Real-time WebSocket Broadcasting                         │
│  • Alert Management                                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   REACT FRONTEND                            │
├─────────────────────────────────────────────────────────────┤
│  • Live Video Display                                       │
│  • Event Timeline                                           │
│  • Alert Dashboard                                          │
│  • Analytics & Statistics                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
ai-service/
│
├── 🔧 Core Modules
│   ├── config.py              # Configuration settings
│   ├── video_processor.py     # Main video processing engine
│   ├── tracker.py             # Object tracking logic
│   ├── event_detector.py      # Security event detection
│   ├── privacy.py             # Face detection & blurring
│   └── utils.py               # Utility functions
│
├── 🌐 API Layer
│   └── app.py                 # Flask REST API server
│
├── 📚 Documentation
│   ├── README.md              # Main documentation
│   ├── API.md                 # API reference
│   └── OVERVIEW.md            # This file
│
├── 🧪 Testing & Examples
│   ├── test_suite.py          # Comprehensive test suite
│   ├── example_file_processing.py    # Video file example
│   └── example_rtsp_stream.py        # RTSP stream example
│
├── 📦 Configuration
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment template
│   ├── .gitignore            # Git ignore rules
│   └── quickstart.sh         # Setup script
│
└── 📂 Data Directories
    ├── uploads/              # Uploaded video files
    └── outputs/              # Processed outputs
```

---

## 🔑 Key Components

### 1. Video Processor (`video_processor.py`)

**Purpose**: Core engine that handles video input, AI processing, and output

**Key Features**:
- Supports both RTSP streams and video files
- Automatic reconnection for RTSP failures
- Frame skipping for performance optimization
- Real-time statistics tracking
- Thread-safe operation

**Usage**:
```python
processor = VideoProcessor("rtsp://camera-url")
processor.set_event_callback(handle_event)
processor.start()
```

---

### 2. Object Tracker (`tracker.py`)

**Purpose**: Maintains persistent object IDs across frames

**Algorithm**: Centroid-based tracking
- Assigns unique IDs to detected objects
- Tracks movement and duration
- Detects stationary objects
- Handles object appearance/disappearance

**Can be upgraded to**: DeepSORT for better accuracy

**Usage**:
```python
tracker = ObjectTracker()
tracked_objects = tracker.update(detections)
duration = tracker.get_object_duration(object_id)
```

---

### 3. Event Detector (`event_detector.py`)

**Purpose**: Analyzes tracked objects to detect security events

**Events Detected**:

1. **Restricted Zone Violation** (Risk: 8/10)
   - Detects people entering prohibited areas
   - Configurable polygon zones

2. **Loitering** (Risk: 6/10)
   - Detects people staying in one area too long
   - Configurable time threshold (default: 5 minutes)

3. **Unattended Object** (Risk: 7/10)
   - Detects bags left alone
   - Distance-based proximity check

4. **Crowd Formation** (Risk: 5/10)
   - Detects high crowd density
   - Detects sudden crowd spikes

**Usage**:
```python
detector = EventDetector()
events = detector.detect_all_events(tracker, tracked_objects, frame_shape)
```

---

### 4. Privacy Module (`privacy.py`)

**Purpose**: Protects individual privacy

**Features**:
- Automatic face detection (Haar Cascade)
- Real-time face blurring
- Configurable blur intensity

**Can be upgraded to**: DNN-based face detection for better accuracy

---

### 5. Flask API (`app.py`)

**Purpose**: HTTP interface for external integration

**Endpoints**:
- `POST /start` - Start processing
- `POST /upload` - Upload video file
- `GET /video` - MJPEG stream
- `GET /stats` - Statistics
- `POST /stop` - Stop processing
- `GET /config` - Configuration
- `GET /health` - Health check

---

## 🚀 Getting Started

### Quick Start (3 steps)

```bash
# 1. Run setup script
./quickstart.sh

# 2. Start the API server
python app.py

# 3. Test with video file or RTSP stream
python example_file_processing.py
# or
python example_rtsp_stream.py
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download YOLO model (automatic on first run)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Configure settings
cp .env.example .env
nano .env

# Run tests
python test_suite.py

# Start server
python app.py
```

---

## ⚙️ Configuration

### Model Selection

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| yolov8n.pt | Fastest | Good | Real-time, limited hardware |
| yolov8s.pt | Fast | Better | Balanced |
| yolov8m.pt | Medium | Great | High accuracy needed |
| yolov8l.pt | Slow | Excellent | Offline processing |

### Event Thresholds

```python
# config.py
LOITERING_THRESHOLD = 300      # 5 minutes
CROWD_THRESHOLD = 10           # 10 people
UNATTENDED_OBJECT_TIME = 30    # 30 seconds
UNATTENDED_OBJECT_DISTANCE = 100  # 100 pixels
```

### Performance Tuning

```python
# config.py
FRAME_SKIP = 0          # Process every frame (0)
                        # Skip frames (1 = every other)

MAX_FRAME_WIDTH = 1280  # Resize large frames
MAX_FRAME_HEIGHT = 720

CONFIDENCE_THRESHOLD = 0.5  # Detection confidence
```

---

## 🔄 Integration Flow

### 1. Start Processing (API Call)

```javascript
// Frontend initiates
fetch('http://localhost:8000/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    source: 'rtsp://camera-url'
  })
})
```

### 2. AI Processing Loop

```
Frame → YOLOv8 → Detections → Tracker → Events → Backend
```

### 3. Event Webhook

```javascript
// Backend receives events
app.post('/api/events', async (req, res) => {
  const event = req.body;
  
  // Save to MongoDB
  await Event.create(event);
  
  // Broadcast to frontend
  io.emit('event', event);
  
  res.json({ success: true });
});
```

### 4. Frontend Display

```javascript
// React component receives event
socket.on('event', (event) => {
  setEvents(prev => [event, ...prev]);
  
  if (event.risk >= 7) {
    showAlert(event);
  }
});
```

---

## 📊 Data Flow

```
RTSP Stream / Video File
         ↓
[Frame Extraction] (OpenCV)
         ↓
[Object Detection] (YOLOv8)
    → person, bag, vehicle
         ↓
[Object Tracking] (Centroid)
    → Assign IDs, Track movement
         ↓
[Event Detection]
    → Analyze patterns
    → Detect anomalies
         ↓
[Privacy Protection]
    → Blur faces
         ↓
[Event Webhook] → Backend API
    → HTTP POST
         ↓
[Database] MongoDB
    → Store events
         ↓
[WebSocket] Socket.IO
    → Broadcast to clients
         ↓
[Frontend] React
    → Display alerts
    → Update timeline
```

---

## 🎨 Customization Examples

### Add Custom Event Type

```python
# event_detector.py

def detect_running_person(self, tracked_objects: Dict) -> List[Dict]:
    """Detect people running (rapid movement)"""
    events = []
    
    for obj_id, obj_info in tracked_objects.items():
        if obj_info['class'] == 'person':
            movement = self.tracker.get_object_movement(obj_id)
            duration = self.tracker.get_object_duration(obj_id)
            
            # Calculate speed (pixels per second)
            if duration > 0:
                speed = movement / duration
                
                if speed > 50:  # Threshold for running
                    events.append({
                        'type': 'running_detected',
                        'object_id': obj_id,
                        'speed': speed,
                        'risk': 4,
                        'description': f'Person running at {speed:.1f} px/s'
                    })
    
    return events
```

### Add Custom Restricted Zone

```python
# config.py

# Define a circular restricted zone
import numpy as np

def generate_circle_zone(center_x, center_y, radius, points=20):
    """Generate circular zone polygon"""
    angles = np.linspace(0, 2*np.pi, points)
    x = center_x + radius * np.cos(angles)
    y = center_y + radius * np.sin(angles)
    return list(zip(x.astype(int), y.astype(int)))

RESTRICTED_ZONES = [
    generate_circle_zone(400, 300, 100)  # Circle at (400,300) r=100
]
```

---

## 🔐 Security Best Practices

### 1. API Authentication

```python
# app.py
API_KEY = os.getenv('API_KEY', 'change-me-in-production')

@app.before_request
def verify_api_key():
    if request.endpoint not in ['health']:
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
```

### 2. HTTPS Only (Production)

```python
# Use nginx or similar as reverse proxy
# Force HTTPS redirects
```

### 3. Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/upload', methods=['POST'])
@limiter.limit("5 per hour")
def upload_video():
    # ...
```

---

## 📈 Performance Benchmarks

### Hardware Requirements

| Configuration | FPS | Resolution | Use Case |
|--------------|-----|------------|----------|
| CPU only (i5) | 10-15 | 720p | Testing |
| CPU only (i7) | 20-25 | 1080p | Small deployments |
| GPU (GTX 1660) | 50-60 | 1080p | Production |
| GPU (RTX 3080) | 100+ | 1080p | High-performance |

### Optimization Tips

1. **Use GPU**: Install CUDA + PyTorch with GPU support
2. **Smaller model**: yolov8n.pt vs yolov8l.pt
3. **Skip frames**: Process every 2nd or 3rd frame
4. **Reduce resolution**: Resize to 720p or lower
5. **Disable face blur**: If not needed

---

## 🐛 Troubleshooting

### Issue: RTSP Connection Fails

**Solution**:
```bash
# Test RTSP URL with FFmpeg
ffmpeg -i rtsp://username:password@ip:port/stream -frames:v 1 test.jpg

# Common RTSP paths:
# rtsp://ip:554/stream1
# rtsp://ip:554/cam/realmonitor?channel=1&subtype=0
# rtsp://ip:554/Streaming/Channels/101
```

### Issue: Low FPS

**Solution**:
```python
# config.py
FRAME_SKIP = 2  # Process every 3rd frame
YOLO_MODEL = "yolov8n.pt"  # Use nano model
MAX_FRAME_WIDTH = 640  # Lower resolution
```

### Issue: Too Many False Positives

**Solution**:
```python
# config.py
CONFIDENCE_THRESHOLD = 0.7  # Increase confidence
```

---

## 🚢 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

### Systemd Service

```ini
[Unit]
Description=AI Video Processing Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-service
ExecStart=/opt/ai-service/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📝 License

MIT License - Free to use in personal and commercial projects.

---

## 🤝 Contributing

This is a modular, extensible codebase. Feel free to:
- Add new event detection algorithms
- Improve tracking accuracy
- Add more YOLO classes
- Enhance privacy features
- Optimize performance

---

## 📞 Support

For issues, questions, or feature requests, please refer to the README.md and API.md documentation.

**Next Steps**:
1. Run `python test_suite.py` to verify setup
2. Try `example_file_processing.py` with a sample video
3. Configure your RTSP camera and test `example_rtsp_stream.py`
4. Integrate with your Node.js backend
5. Build your React frontend dashboard

**Happy Monitoring! 🎥🤖**