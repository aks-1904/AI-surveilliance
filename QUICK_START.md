# 🚀 Quick Start Guide

## For AI Service Developers (You!)

### Installation (5 minutes)

1. **Navigate to ai-service directory**
```bash
cd ai-service
```

2. **Create virtual environment**
```bash
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment**
```bash
cp .env.example .env
```

5. **Start the service**
```bash
python app.py
```

### First Test (2 minutes)

```bash
# Test 1: Health check
curl http://localhost:5000/health

# Test 2: Start camera
curl -X POST http://localhost:5000/start

# Test 3: Add a test zone
curl -X POST http://localhost:5000/zones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Zone",
    "polygon": [
      {"x": 100, "y": 100},
      {"x": 400, "y": 100},
      {"x": 400, "y": 400},
      {"x": 100, "y": 400}
    ]
  }'
```

### Demo the Features (5 minutes)

1. **Person Detection**
   - Stand in front of camera
   - See bounding box (if DEBUG_MODE=True)

2. **Zone Intrusion**
   - Walk into the zone you created
   - Check console for "Zone intrusion" message

3. **Loitering**
   - Stand still for 30+ seconds
   - Watch for "Loitering detected" message

---

## For Backend Developers

See `INTEGRATION_GUIDE.md` → Section: "BACKEND DEVELOPER GUIDE"

### Quick Checklist
- [ ] Install Node.js dependencies
- [ ] Setup MongoDB Atlas
- [ ] Create .env file with MONGODB_URI
- [ ] Start server: `npm run dev`
- [ ] Test endpoint: `POST /api/events`
- [ ] Setup WebSocket
- [ ] Test zone sync with AI service

---

## For Frontend Developers

See `INTEGRATION_GUIDE.md` → Section: "FRONTEND DEVELOPER GUIDE"

### Quick Checklist
- [ ] Create React app
- [ ] Install dependencies (socket.io-client, axios, react-konva)
- [ ] Setup Socket.IO connection
- [ ] Create Dashboard component
- [ ] Test WebSocket alerts
- [ ] Implement Zone Drawer
- [ ] Connect to backend API

---

## System Architecture at a Glance

```
User → Frontend (React)
         ↓ WebSocket
      Backend (Node.js)
         ↓ HTTP Events
      AI Service (Python)
         ↓ OpenCV + YOLO
      Webcam
```

---

## Demo Flow

1. **Start all 3 services**
   - AI Service: `python app.py`
   - Backend: `npm run dev`
   - Frontend: `npm start`

2. **Open Dashboard**
   - Click "Start Camera"

3. **Draw Restricted Zone**
   - Click "Draw Zone"
   - Click 4 points on video
   - Name it and save

4. **Trigger Event**
   - Walk into zone
   - See alert appear in real-time

5. **Show to Judges**
   - Point out face blurring (privacy)
   - Show risk score calculation
   - Demonstrate loitering detection
   - Show event timeline

---

## Troubleshooting

### Camera won't start
```bash
# Check available cameras
python -c "import cv2; print([cv2.VideoCapture(i).isOpened() for i in range(3)])"
```

### Backend can't connect to AI Service
- Check both services are running
- Verify ports (AI: 5000, Backend: 3000)
- Check BACKEND_URL in AI service .env

### Frontend not receiving alerts
- Check WebSocket connection in browser console
- Verify backend WebSocket is configured
- Test with Postman WebSocket client

---

## Key Files to Understand

### AI Service
- `app.py` - Main application, routes
- `detection/person_detector.py` - YOLO detection
- `analysis/zone_analyzer.py` - Zone checking
- `risk/risk_engine.py` - Risk calculation
- `utils/event_publisher.py` - Backend communication

### Backend (to be built)
- `server.js` - Express + Socket.IO
- `models/Event.js` - MongoDB schema
- `routes/events.js` - Event endpoints

### Frontend (to be built)
- `Dashboard.jsx` - Main page
- `ZoneDrawer.jsx` - Interactive zone creation
- `AlertPanel.jsx` - Real-time alerts

---

## What Makes This Project Stand Out

✅ **Real AI** - Actual YOLOv8 detection, not fake  
✅ **Privacy First** - Face blurring built-in  
✅ **Modular** - Clean, professional code structure  
✅ **Real-time** - WebSocket alerts, no polling  
✅ **Interactive** - User draws zones on video  
✅ **Smart** - Risk scoring, loitering, unattended objects  
✅ **Production-ready** - Error handling, logging, config  

---

## Next Steps

1. **Test AI Service** thoroughly
2. **Share INTEGRATION_GUIDE.md** with backend/frontend devs
3. **Build backend** following the guide
4. **Build frontend** following the guide
5. **Integration testing**
6. **Prepare demo**
7. **Win hackathon** 🏆

---

**Questions?** Check README.md and INTEGRATION_GUIDE.md