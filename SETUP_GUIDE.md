# 🚀 Complete Setup Guide

Step-by-step instructions to get the AI Surveillance Co-Pilot running.

## Table of Contents
1. [Prerequisites Check](#prerequisites-check)
2. [MongoDB Setup](#mongodb-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Integration Testing](#integration-testing)
6. [Common Issues](#common-issues)

---

## Prerequisites Check

Before starting, ensure you have:

### Required Software

```bash
# Check Node.js version (need 16+)
node --version

# Check npm
npm --version

# Check Python version (AI service - need 3.8+)
python --version
# or
python3 --version
```

If any are missing:
- **Node.js**: Download from https://nodejs.org/
- **Python**: Download from https://python.org/

---

## MongoDB Setup

### Option 1: MongoDB Atlas (Recommended)

1. **Create Account**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free account

2. **Create Cluster**
   - Click "Build a Database"
   - Select "Free" tier
   - Choose cloud provider and region
   - Click "Create Cluster"

3. **Setup Database User**
   - Go to "Database Access"
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: `surveillance_user`
   - Password: Generate strong password (save it!)
   - Database User Privileges: "Read and write to any database"
   - Click "Add User"

4. **Configure Network Access**
   - Go to "Network Access"
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (for development)
   - Click "Confirm"

5. **Get Connection String**
   - Go to "Database" → "Connect"
   - Choose "Connect your application"
   - Driver: Node.js, Version: 4.1 or later
   - Copy connection string
   - Replace `<password>` with your password
   - Replace `myFirstDatabase` with `surveillance`
   
   Example: 
   ```
   mongodb+srv://surveillance_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/surveillance?retryWrites=true&w=majority
   ```

### Option 2: Local MongoDB

```bash
# Install MongoDB locally
# macOS:
brew tap mongodb/brew
brew install mongodb-community

# Ubuntu:
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
sudo apt-get install mongodb-org

# Start MongoDB
mongod --dbpath=/path/to/data/directory
```

Connection string for local: `mongodb://localhost:27017/surveillance`

---

## Backend Setup

### Step 1: Install Dependencies

```bash
cd backend
npm install
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file:

```env
# Server
PORT=3000
NODE_ENV=development

# MongoDB - PASTE YOUR CONNECTION STRING HERE
MONGODB_URI=mongodb+srv://surveillance_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/surveillance?retryWrites=true&w=majority

# AI Service
AI_SERVICE_URL=http://localhost:5000

# Frontend
FRONTEND_URL=http://localhost:3001

# CORS
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3000
```

⚠️ **Important**: Replace `YOUR_PASSWORD` and the cluster address with your actual MongoDB details!

### Step 3: Test Backend

```bash
# Start in development mode
npm run dev
```

You should see:

```
MongoDB Connected: cluster0-shard-00-00.xxxxx.mongodb.net
Database: surveillance
🚀 AI Surveillance Co-Pilot Backend Server
Server running on port 3000
```

### Step 4: Test API

Open new terminal:

```bash
# Test health endpoint
curl http://localhost:3000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Surveillance Backend",
  "mongodb": {
    "status": "connected"
  },
  "websocket": {
    "connected_clients": 0
  }
}
```

✅ Backend is ready!

---

## Frontend Setup

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

This may take a few minutes.

### Step 2: Configure Environment

```bash
cp .env.example .env
```

The default `.env` should work:

```env
REACT_APP_BACKEND_URL=http://localhost:3000
REACT_APP_AI_SERVICE_URL=http://localhost:5000
REACT_APP_VIDEO_STREAM_URL=http://localhost:5000/video_feed
```

### Step 3: Start Frontend

```bash
npm start
```

Browser should automatically open to http://localhost:3001

You should see:
- AI Surveillance Co-Pilot dashboard
- "Disconnected" status (normal - backend needs to be running)
- Empty stats and alerts

### Step 4: Test Connection

1. Make sure **backend is still running** (from previous step)
2. Refresh the frontend page
3. Status should change to "Connected" (green)

✅ Frontend is ready!

---

## Integration Testing

Now test that everything works together:

### Test 1: WebSocket Connection

1. Frontend should show "Connected" status (green)
2. Check browser console (F12) - should see:
   ```
   [Socket] Connected: xxxxx
   ```

### Test 2: Create a Zone

1. Click "Draw Zone" button
2. Enter name: "Test Zone"
3. Click "Start Drawing"
4. Click 4 points on the canvas to create a rectangle
5. Click "Save Zone"
6. Should see success message
7. Backend terminal should show:
   ```
   [ZONE CREATED] Test Zone - Synced with AI service
   ```

### Test 3: Verify Database

Check MongoDB Atlas:
1. Go to "Database" → "Browse Collections"
2. Select `surveillance` database
3. Should see collections: `events`, `zones`, `alerts`
4. Click on `zones` - should see your test zone

### Test 4: API Endpoints

```bash
# Get zones
curl http://localhost:3000/api/zones

# Get events
curl http://localhost:3000/api/events

# Get analytics
curl http://localhost:3000/api/analytics/summary
```

All should return valid JSON responses.

---

## Running with AI Service

If you have the AI service ready:

### Terminal 1: AI Service

```bash
cd ai-service
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```

### Terminal 2: Backend

```bash
cd backend
npm run dev
```

### Terminal 3: Frontend

```bash
cd frontend
npm start
```

### Test Full Flow

1. Open dashboard (http://localhost:3001)
2. Click "Start Camera"
3. Camera should activate
4. Draw a zone
5. Walk into the zone
6. Alert should appear in real-time!

---

## Common Issues

### Issue: MongoDB Connection Failed

**Error**: `MongooseServerSelectionError`

**Solutions**:
1. Check connection string is correct
2. Verify password has no special characters (use URL encoding if needed)
3. Check IP whitelist in MongoDB Atlas
4. Try "Allow Access from Anywhere" temporarily

### Issue: Backend Port Already in Use

**Error**: `EADDRINUSE: address already in use`

**Solutions**:
```bash
# Find process using port 3000
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Issue: Frontend Won't Start

**Error**: `npm ERR! code ELIFECYCLE`

**Solutions**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue: WebSocket Not Connecting

**Symptoms**: Frontend shows "Disconnected"

**Solutions**:
1. Ensure backend is running
2. Check backend URL in frontend `.env`
3. Look for CORS errors in browser console
4. Restart both backend and frontend

### Issue: Video Feed Not Loading

**Solutions**:
1. Ensure AI service is running
2. Click "Start Camera" in dashboard
3. Check REACT_APP_VIDEO_STREAM_URL in frontend `.env`
4. Verify webcam is accessible

---

## Verification Checklist

Before considering setup complete:

- [ ] MongoDB connection successful
- [ ] Backend health check returns `status: "healthy"`
- [ ] Frontend shows "Connected" status
- [ ] Can create zones successfully
- [ ] Analytics endpoint returns data
- [ ] WebSocket events working (test by creating zone)
- [ ] Browser console shows no errors

---

## Next Steps

Once everything is working:

1. **Test AI Integration**
   - Start AI service
   - Start camera
   - Test person detection

2. **Create Actual Zones**
   - Draw zones for your monitoring area
   - Name them appropriately
   - Test intrusion detection

3. **Monitor Events**
   - Watch for real-time alerts
   - Check event timeline
   - Review analytics

4. **Production Deployment**
   - Use production MongoDB cluster
   - Enable HTTPS
   - Set up proper authentication
   - Configure reverse proxy (nginx)

---

## Getting Help

If you encounter issues:

1. Check the logs in each terminal
2. Review the troubleshooting section
3. Verify environment variables
4. Check MongoDB Atlas connection
5. Test each service independently

---

## Success! 🎉

If you've completed all steps, your AI Surveillance Co-Pilot is ready to use!

Access the dashboard at: **http://localhost:3001**

Happy monitoring! 👁️