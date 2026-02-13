# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
# AI Surveillance Co-Pilot - Frontend

React-based frontend dashboard for the AI Surveillance system with real-time alerts and zone management.

## Features

- ✅ Real-time video feed display
- ✅ WebSocket-based live alerts
- ✅ Interactive zone drawing on video
- ✅ Event timeline and statistics
- ✅ Risk scoring and indicators
- ✅ Responsive dashboard design
- ✅ Browser notifications

## Prerequisites

- Node.js 16+ and npm
- Backend server running on port 3000
- AI Service running on port 5000

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

The default configuration should work if all services use standard ports.

### 3. Start Development Server

```bash
npm start
```

Application will open at http://localhost:3001

## Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Components

### Pages
- **Dashboard** - Main application page with all features

### Components
- **VideoPlayer** - Displays live video stream from AI service
- **ZoneDrawer** - Interactive canvas for drawing restricted zones
- **AlertPanel** - Real-time alert display with acknowledge buttons
- **StatsCard** - Statistical information cards
- **RiskIndicator** - Current risk level display

### Services
- **api.js** - Backend API communication
- **socket.js** - WebSocket/Socket.IO management

### Hooks
- **useSocket** - Custom hook for WebSocket state management

## API Integration

The frontend communicates with:

1. **Backend API** (http://localhost:3000/api)
   - Event management
   - Zone CRUD operations
   - Analytics data
   - Alert management

2. **AI Service** (http://localhost:5000)
   - Camera control (start/stop)
   - Video feed stream
   - System statistics

## WebSocket Events

The frontend listens for these real-time events:

- `alert` - New security event detected
- `stats_update` - Statistics refresh
- `zone_created` - New zone added
- `zone_updated` - Zone modified
- `zone_deleted` - Zone removed
- `event_acknowledged` - Event marked as handled
- `heartbeat` - Server health check

## Features Guide

### Starting Camera
1. Click "Start Camera" button
2. AI service begins processing
3. Live feed appears in video player

### Drawing Zones
1. Click "Draw Zone" button
2. Enter zone name
3. Click "Start Drawing"
4. Click on video to add points (minimum 3)
5. Click "Save Zone"

### Handling Alerts
- Alerts appear in real-time in the right panel
- Click checkmark to acknowledge
- Recent alerts show at top
- Color-coded by risk level

### Viewing Analytics
- Statistics update automatically
- 24-hour event summaries
- Risk distribution charts
- Event type breakdown

## Environment Variables

Create `.env` file with:

```env
REACT_APP_BACKEND_URL=http://localhost:3000
REACT_APP_AI_SERVICE_URL=http://localhost:5000
REACT_APP_VIDEO_STREAM_URL=http://localhost:5000/video_feed
```

## Styling

Built with Tailwind CSS for:
- Responsive design
- Utility-first styling
- Custom components
- Dark mode support

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari

**Note:** WebSocket and browser notifications require modern browsers.

## Troubleshooting

### Video Feed Not Loading
1. Ensure AI service is running
2. Check REACT_APP_VIDEO_STREAM_URL
3. Verify camera is started
4. Check browser console for errors

### WebSocket Not Connecting
1. Verify backend is running
2. Check REACT_APP_BACKEND_URL
3. Look for CORS errors
4. Try refreshing the page

### Zones Not Saving
1. Check backend connection
2. Verify minimum 3 points drawn
3. Check console for validation errors
4. Ensure unique zone name

## Development

### Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── VideoPlayer.jsx
│   │   ├── ZoneDrawer.jsx
│   │   ├── AlertPanel.jsx
│   │   ├── StatsCard.jsx
│   │   └── RiskIndicator.jsx
│   ├── pages/
│   │   └── Dashboard.jsx
│   ├── services/
│   │   ├── api.js
│   │   └── socket.js
│   ├── hooks/
│   │   └── useSocket.js
│   ├── App.js
│   ├── index.js
│   └── index.css
├── package.json
└── tailwind.config.js
```

### Adding New Features

1. **New Component**: Create in `src/components/`
2. **New Page**: Create in `src/pages/`
3. **New API Call**: Add to `src/services/api.js`
4. **New Hook**: Create in `src/hooks/`

## Performance

- React optimizations for smooth rendering
- WebSocket for efficient real-time updates
- Lazy loading for large datasets
- Memoization for expensive computations

## Security

- HTTPS support in production
- CORS protection
- No sensitive data in frontend
- Secure WebSocket connections

## License

MIT