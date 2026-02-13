# AI Surveillance Co-Pilot - Backend

Node.js backend server with Express, MongoDB, and Socket.IO for the AI Surveillance system.

## Features

- ✅ RESTful API for events, zones, analytics, and alerts
- ✅ Real-time WebSocket communication
- ✅ MongoDB database with Mongoose ODM
- ✅ Comprehensive error handling
- ✅ Input validation
- ✅ Modular route structure
- ✅ AI service integration

## Prerequisites

- Node.js 16+ and npm
- MongoDB Atlas account (or local MongoDB)
- AI Service running on port 5000

## Quick Start

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your MongoDB connection string:

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/surveillance?retryWrites=true&w=majority
```

### 3. Start Server

Development mode (with auto-reload):
```bash
npm run dev
```

Production mode:
```bash
npm start
```

Server will start on http://localhost:3000

## API Endpoints

### Events API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/events` | Create new event (from AI service) |
| GET | `/api/events` | Get all events (with filters) |
| GET | `/api/events/:id` | Get single event |
| PUT | `/api/events/:id/acknowledge` | Acknowledge event |
| DELETE | `/api/events/:id` | Delete event |
| GET | `/api/events/stats/summary` | Get event statistics |

### Zones API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/zones` | Create new zone |
| GET | `/api/zones` | Get all zones |
| GET | `/api/zones/:id` | Get single zone |
| PUT | `/api/zones/:id` | Update zone |
| DELETE | `/api/zones/:id` | Delete zone |
| POST | `/api/zones/sync` | Sync zones with AI service |

### Analytics API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/summary` | Get analytics summary |
| GET | `/api/analytics/timeline` | Get hourly timeline |
| GET | `/api/analytics/heatmap` | Get location heatmap |
| GET | `/api/analytics/trends` | Get trend analysis |
| GET | `/api/analytics/zones` | Get zone statistics |
| GET | `/api/analytics/alerts` | Get alert statistics |

### Alerts API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | Get all alerts |
| GET | `/api/alerts/unread` | Get unread alerts |
| PUT | `/api/alerts/:id/read` | Mark alert as read |
| PUT | `/api/alerts/:id/dismiss` | Dismiss alert |
| POST | `/api/alerts/mark-all-read` | Mark all as read |

### Health Check

```bash
GET /api/health
```

## WebSocket Events

### Server -> Client

- `alert` - New event alert
- `stats_update` - Statistics updated
- `zone_created` - New zone created
- `zone_updated` - Zone updated
- `zone_deleted` - Zone deleted
- `event_acknowledged` - Event acknowledged
- `alert_read` - Alert marked as read
- `alert_dismissed` - Alert dismissed
- `heartbeat` - Server health status (every 30s)
- `client_count` - Connected clients count

### Client -> Server

- `subscribe` - Subscribe to specific channels
- `unsubscribe` - Unsubscribe from channels
- `ping` - Connection keepalive

## Testing

### Test Health Endpoint

```bash
curl http://localhost:3000/api/health
```

### Test Event Creation

```bash
curl -X POST http://localhost:3000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "RESTRICTED_ENTRY",
    "timestamp": "2024-02-13T10:30:00Z",
    "location": {"x": 250, "y": 180},
    "details": {"message": "Test intrusion"},
    "risk_score": 8,
    "risk_level": "HIGH",
    "metadata": {"person_id": 1, "zone_id": 1}
  }'
```

### Test Zone Creation

```bash
curl -X POST http://localhost:3000/api/zones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Server Room",
    "polygon": [
      {"x": 100, "y": 100},
      {"x": 300, "y": 100},
      {"x": 300, "y": 300},
      {"x": 100, "y": 300}
    ],
    "description": "High security zone"
  }'
```

## Project Structure

```
backend/
├── server.js              # Main application entry
├── package.json           # Dependencies
├── .env.example          # Environment template
├── .env                  # Environment variables (create this)
│
├── models/               # MongoDB schemas
│   ├── Event.js         # Event model
│   ├── Zone.js          # Zone model
│   └── Alert.js         # Alert model
│
├── routes/              # API routes
│   ├── events.js       # Event endpoints
│   ├── zones.js        # Zone endpoints
│   ├── analytics.js    # Analytics endpoints
│   └── alerts.js       # Alert endpoints
│
└── middleware/          # Custom middleware
    ├── validation.js   # Input validation
    └── errorHandler.js # Error handling
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Server port | 3000 |
| NODE_ENV | Environment | development |
| MONGODB_URI | MongoDB connection string | Required |
| AI_SERVICE_URL | AI service URL | http://localhost:5000 |
| FRONTEND_URL | Frontend URL for CORS | http://localhost:3001 |
| ALLOWED_ORIGINS | CORS origins (comma-separated) | http://localhost:3001 |

## Database Schema

### Event Collection

```javascript
{
  event_type: "RESTRICTED_ENTRY" | "LOITERING" | "UNATTENDED_OBJECT",
  timestamp: Date,
  location: { x: Number, y: Number },
  details: {
    message: String,
    bbox: [Number],
    person_id: Number,
    zone_id: Number,
    duration: Number
  },
  risk_score: Number (0-10),
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  acknowledged: Boolean,
  acknowledged_at: Date,
  acknowledged_by: String
}
```

### Zone Collection

```javascript
{
  name: String,
  polygon: [{ x: Number, y: Number }],
  active: Boolean,
  created_by: String,
  description: String,
  color: String,
  risk_multiplier: Number
}
```

### Alert Collection

```javascript
{
  event_id: ObjectId,
  alert_type: "RESTRICTED_ENTRY" | "LOITERING" | "UNATTENDED_OBJECT",
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  message: String,
  read: Boolean,
  dismissed: Boolean
}
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "Error message",
  "field": "field_name",
  "details": []
}
```

HTTP Status Codes:
- 200: Success
- 201: Created
- 400: Bad Request (validation error)
- 404: Not Found
- 409: Conflict (duplicate)
- 500: Internal Server Error

## Logging

The server logs:
- All HTTP requests
- WebSocket connections/disconnections
- Event creation
- Zone creation/updates
- Errors and warnings

## Performance

- MongoDB indexes for fast queries
- Pagination on list endpoints
- Aggregation pipelines for analytics
- Connection pooling
- Graceful shutdown

## Security

- CORS protection
- Input validation
- MongoDB injection prevention
- Error message sanitization
- Environment variable protection

## Troubleshooting

### MongoDB Connection Failed

1. Check your connection string in `.env`
2. Ensure IP whitelist in MongoDB Atlas
3. Verify credentials

### WebSocket Not Connecting

1. Check FRONTEND_URL in `.env`
2. Verify CORS settings
3. Check firewall/proxy settings

### AI Service Communication Failed

1. Ensure AI service is running
2. Check AI_SERVICE_URL in `.env`
3. Test AI service health endpoint

## Development

### Add New Route

1. Create route file in `routes/`
2. Import in `server.js`
3. Add to app: `app.use('/api/yourroute', yourRouter)`

### Add New Model

1. Create schema in `models/`
2. Define validation and methods
3. Export model

### Add Validation

1. Add validation function in `middleware/validation.js`
2. Use in route: `router.post('/', validateYourData, handler)`

## License

MIT