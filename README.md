# 🎥 AI Surveillance Co-Pilot

A complete AI-powered surveillance system with real-time person detection, zone intrusion alerts, and intelligent risk scoring.

## 🌟 Features

- ✅ **Real-time Person Detection** - YOLOv8-based detection
- ✅ **Zone Intrusion Detection** - Custom restricted zones
- ✅ **Loitering Detection** - Track stationary persons
- ✅ **Unattended Object Detection** - Identify left items
- ✅ **Risk Scoring** - AI-powered threat assessment
- ✅ **Face Blurring** - Privacy protection
- ✅ **Real-time Alerts** - WebSocket notifications
- ✅ **Interactive Dashboard** - React-based UI
- ✅ **Zone Drawing** - Draw zones on live video
- ✅ **Analytics** - Comprehensive event statistics

## 🏗️ Architecture

```
┌──────────────┐      HTTP Events      ┌──────────────┐
│  AI Service  │ ──────────────────→   │   Backend    │
│   (Python)   │                        │  (Node.js)   │
│   Port 5000  │                        │  Port 3000   │
└──────────────┘                        └──────────────┘
                                               ↓
                                        WebSocket Events
                                               ↓
                                        ┌──────────────┐
                                        │   Frontend   │
                                        │    (React)   │
                                        │  Port 3001   │
                                        └──────────────┘
                                               ↓
                                        ┌──────────────┐
                                        │   MongoDB    │
                                        │   (Atlas)    │
                                        └──────────────┘
```

## 📋 Prerequisites

- **Python 3.8+** (for AI service)
- **Node.js 16+** (for backend & frontend)
- **MongoDB Atlas** account (or local MongoDB)
- **Webcam** or video source

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd surveillance-system
```

### 2. Setup AI Service

```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python app.py
```

AI Service will start on http://localhost:5000

### 3. Setup Backend

```bash
cd backend
npm install
cp .env.example .env
# Edit .env with your MongoDB URI
npm run dev
```

Backend will start on http://localhost:3000

### 4. Setup Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm start
```

Frontend will open at http://localhost:3001

## 📁 Project Structure

```
surveillance-system/
├── ai-service/          # Python AI detection service
│   ├── app.py          # Flask application
│   ├── detection/      # YOLO detection modules
│   ├── analysis/       # Zone & behavior analysis
│   ├── risk/           # Risk scoring engine
│   └── utils/          # Helpers & event publisher
│
├── backend/            # Node.js Express backend
│   ├── server.js       # Main server
│   ├── models/         # MongoDB schemas
│   ├── routes/         # API routes
│   └── middleware/     # Validation & error handling
│
└── frontend/           # React dashboard
    ├── src/
    │   ├── components/ # React components
    │   ├── pages/      # Page components
    │   ├── services/   # API & Socket services
    │   └── hooks/      # Custom hooks
    └── public/         # Static files
```

## 🎯 Usage Guide

### Starting the System

1. **Start all three services** in separate terminals
2. **Open dashboard** at http://localhost:3001
3. **Click "Start Camera"** to begin monitoring
4. **Draw zones** using the "Draw Zone" button
5. **Monitor alerts** in the right panel

### Drawing Restricted Zones

1. Click "Draw Zone" button
2. Enter zone name (e.g., "Server Room")
3. Click "Start Drawing"
4. Click on video to place points (minimum 3)
5. Click "Save Zone" when done

### Handling Alerts

- Alerts appear automatically when events are detected
- Click ✓ to acknowledge
- View full event details
- Check risk scores and event types

## 🔧 Configuration

### AI Service (.env)

```env
BACKEND_URL=http://localhost:3000
CAMERA_INDEX=0
DEBUG_MODE=False
LOITERING_THRESHOLD=30
```

### Backend (.env)

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/surveillance
AI_SERVICE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:3001
PORT=3000
```

### Frontend (.env)

```env
REACT_APP_BACKEND_URL=http://localhost:3000
REACT_APP_AI_SERVICE_URL=http://localhost:5000
```

## 📊 API Documentation

### Backend Endpoints

**Events**
- `POST /api/events` - Create event
- `GET /api/events` - List events
- `PUT /api/events/:id/acknowledge` - Acknowledge event

**Zones**
- `POST /api/zones` - Create zone
- `GET /api/zones` - List zones
- `DELETE /api/zones/:id` - Delete zone

**Analytics**
- `GET /api/analytics/summary` - Get statistics
- `GET /api/analytics/timeline` - Hourly timeline
- `GET /api/analytics/trends` - Trend analysis

### AI Service Endpoints

- `POST /start` - Start camera
- `POST /stop` - Stop camera
- `GET /video_feed` - Live video stream
- `POST /zones` - Add restricted zone
- `GET /stats` - Detection statistics

## 🧪 Testing

### Test Backend

```bash
curl http://localhost:3000/api/health
```

### Test Event Creation

```bash
curl -X POST http://localhost:3000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "RESTRICTED_ENTRY",
    "risk_score": 8,
    "risk_level": "HIGH"
  }'
```

### Test Zone Creation

```bash
curl -X POST http://localhost:3000/api/zones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Zone",
    "polygon": [
      {"x": 100, "y": 100},
      {"x": 300, "y": 100},
      {"x": 300, "y": 300},
      {"x": 100, "y": 300}
    ]
  }'
```

## 🐛 Troubleshooting

### Camera Won't Start
- Check camera permissions
- Verify CAMERA_INDEX in AI service .env
- Ensure no other app is using the camera

### MongoDB Connection Failed
- Verify connection string
- Check IP whitelist in MongoDB Atlas
- Confirm credentials

### WebSocket Not Connecting
- Ensure backend is running
- Check FRONTEND_URL in backend .env
- Verify CORS settings

### Video Feed Not Displaying
- Start camera from dashboard
- Check AI service is running
- Verify network connectivity

## 🔒 Security Features

- **Face Blurring** - Automatic privacy protection
- **Input Validation** - Prevents injection attacks
- **CORS Protection** - Secure cross-origin requests
- **Error Handling** - Safe error messages
- **MongoDB Injection Prevention** - Parameterized queries

## 📈 Performance

- **Real-time Processing** - 15-30 FPS detection
- **Efficient WebSockets** - Low latency alerts
- **Database Indexing** - Fast query performance
- **Connection Pooling** - Optimized MongoDB access

## 🎓 Key Technologies

- **AI Detection**: YOLOv8, OpenCV
- **Backend**: Node.js, Express, Socket.IO, MongoDB
- **Frontend**: React, Tailwind CSS, React Konva
- **Real-time**: WebSocket, Server-Sent Events

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues or questions:
- Check troubleshooting guide
- Review API documentation
- Check logs in each service

## 🏆 Credits

Built with ❤️ for intelligent surveillance and security monitoring.