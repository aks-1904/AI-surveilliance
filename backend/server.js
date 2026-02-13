const express = require('express');
const mongoose = require('mongoose');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const bodyParser = require('body-parser');
require('dotenv').config();

// Import routes
const eventsRouter = require('./routes/events');
const zonesRouter = require('./routes/zones');
const analyticsRouter = require('./routes/analytics');
const alertsRouter = require('./routes/alerts');

// Import middleware
const { errorHandler, notFound } = require('./middleware/errorHandler');

// Initialize Express app
const app = express();
const server = http.createServer(app);

// Initialize Socket.IO with CORS
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3001',
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    credentials: true
  }
});

// Middleware
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3001'],
  credentials: true
}));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// MongoDB Connection
const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });
    
    console.log(`MongoDB Connected: ${conn.connection.host}`);
    console.log(`Database: ${conn.connection.name}`);
  } catch (error) {
    console.error('MongoDB connection error:', error);
    process.exit(1);
  }
};

connectDB();

// MongoDB event listeners
mongoose.connection.on('error', (err) => {
  console.error('MongoDB error:', err);
});

mongoose.connection.on('disconnected', () => {
  console.warn('MongoDB disconnected. Attempting to reconnect...');
});

// Make io accessible to routes
app.set('io', io);

// Health check endpoint
app.get('/api/health', (req, res) => {
  const health = {
    status: 'healthy',
    service: 'Surveillance Backend',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    mongodb: {
      status: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
      host: mongoose.connection.host,
      database: mongoose.connection.name
    },
    websocket: {
      connected_clients: io.engine.clientsCount,
      status: 'active'
    }
  };
  
  res.json(health);
});

// API Routes
app.use('/api/events', eventsRouter);
app.use('/api/zones', zonesRouter);
app.use('/api/analytics', analyticsRouter);
app.use('/api/alerts', alertsRouter);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'AI Surveillance Co-Pilot Backend API',
    version: '1.0.0',
    endpoints: {
      health: '/api/health',
      events: '/api/events',
      zones: '/api/zones',
      analytics: '/api/analytics',
      alerts: '/api/alerts'
    },
    documentation: 'See README.md for API documentation'
  });
});

// WebSocket connection handling
io.on('connection', (socket) => {
  console.log(`[WebSocket] Client connected: ${socket.id}`);
  
  // Send current connection count to all clients
  io.emit('client_count', io.engine.clientsCount);
  
  // Handle client subscription to specific event types
  socket.on('subscribe', (data) => {
    console.log(`[WebSocket] Client ${socket.id} subscribed to:`, data);
    socket.join(data.channel || 'default');
  });
  
  // Handle client unsubscription
  socket.on('unsubscribe', (data) => {
    console.log(`[WebSocket] Client ${socket.id} unsubscribed from:`, data);
    socket.leave(data.channel || 'default');
  });
  
  // Handle ping for connection keepalive
  socket.on('ping', () => {
    socket.emit('pong');
  });
  
  // Handle disconnection
  socket.on('disconnect', (reason) => {
    console.log(`[WebSocket] Client disconnected: ${socket.id} - Reason: ${reason}`);
    io.emit('client_count', io.engine.clientsCount);
  });
  
  // Handle errors
  socket.on('error', (error) => {
    console.error(`[WebSocket] Socket error for ${socket.id}:`, error);
  });
});

// Periodic WebSocket health broadcast (every 30 seconds)
setInterval(() => {
  io.emit('heartbeat', {
    timestamp: new Date().toISOString(),
    server_status: 'healthy',
    connected_clients: io.engine.clientsCount
  });
}, 30000);

// 404 handler
app.use(notFound);

// Error handler (must be last)
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log('\n' + '='.repeat(60));
  console.log('🚀 AI Surveillance Co-Pilot Backend Server');
  console.log('='.repeat(60));
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`API URL: http://localhost:${PORT}`);
  console.log(`WebSocket: ws://localhost:${PORT}`);
  console.log('='.repeat(60) + '\n');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received. Shutting down gracefully...');
  server.close(() => {
    console.log('Server closed');
    mongoose.connection.close(false, () => {
      console.log('MongoDB connection closed');
      process.exit(0);
    });
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received. Shutting down gracefully...');
  server.close(() => {
    console.log('Server closed');
    mongoose.connection.close(false, () => {
      console.log('MongoDB connection closed');
      process.exit(0);
    });
  });
});

module.exports = { app, server, io };