# WebSocket Configuration Guide for OpenHands

This guide helps you set up WebSocket connections correctly for OpenHands in various environments.

## Quick Start

### Using the Startup Script

The easiest way to start OpenHands with proper WebSocket configuration:

```bash
./start_openhands.sh
```

This script automatically:
- Configures the backend and frontend servers
- Sets up WebSocket with CORS support
- Uses the correct ports for your environment
- Enables debug mode for troubleshooting

### Manual Configuration

If you prefer to configure manually:

1. **Backend Configuration** (Port 12000):
```bash
export BACKEND_HOST=0.0.0.0
export BACKEND_PORT=12000
poetry run uvicorn openhands.server.listen:app --host 0.0.0.0 --port 12000
```

2. **Frontend Configuration** (Port 12001):
```bash
cd frontend
export VITE_BACKEND_HOST="0.0.0.0:12000"
export VITE_FRONTEND_PORT=12001
npm run dev -- --port 12001 --host 0.0.0.0
```

## WebSocket Architecture

### Backend (Socket.IO Server)
- **File**: `openhands/server/shared.py`
- **Configuration**: AsyncServer with CORS enabled
- **Events**: `connect`, `disconnect`, `oh_user_action`, `oh_event`
- **Transport**: WebSocket only (no polling fallback)

### Frontend (Socket.IO Client)
- **File**: `frontend/src/context/ws-client-provider.tsx`
- **Connection**: Automatic reconnection with event replay
- **Transport**: WebSocket only (`transports: ["websocket"]`)

### Proxy Configuration
The frontend Vite server proxies WebSocket connections:
```javascript
"/socket.io": {
  target: WS_URL,
  ws: true,
  changeOrigin: true,
  secure: !INSECURE_SKIP_VERIFY,
}
```

## Environment Variables

### Backend
- `BACKEND_HOST`: Host to bind the backend server (default: 0.0.0.0)
- `BACKEND_PORT`: Port for the backend server (default: 12000)
- `DEBUG`: Enable debug logging (default: true)
- `CORS_ALLOWED_ORIGINS`: CORS origins (default: *)

### Frontend
- `VITE_BACKEND_HOST`: Backend host:port for API calls
- `VITE_FRONTEND_PORT`: Frontend development server port
- `VITE_USE_TLS`: Use HTTPS/WSS (default: false)
- `VITE_INSECURE_SKIP_VERIFY`: Skip TLS verification (default: true)

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if backend is running on the correct port
   - Verify CORS configuration
   - Ensure firewall allows WebSocket connections

2. **Frontend Can't Connect to Backend**
   - Verify `VITE_BACKEND_HOST` points to the correct backend
   - Check proxy configuration in `vite.config.ts`
   - Ensure both servers are running

3. **Events Not Received**
   - Check browser developer console for WebSocket errors
   - Verify event handlers are properly registered
   - Enable debug mode to see detailed logs

### Debug Commands

Check if services are running:
```bash
# Check backend
curl http://localhost:12000/api/health

# Check frontend
curl http://localhost:12001

# Check WebSocket connection
wscat -c ws://localhost:12000/socket.io/?EIO=4&transport=websocket
```

Monitor logs:
```bash
# Backend logs (if running with the script)
tail -f logs/backend.log

# Frontend logs
# Check browser developer console -> Network -> WS tab
```

### Network Configuration

For remote deployments, ensure:
1. Ports 12000 and 12001 are accessible
2. WebSocket upgrade headers are allowed
3. Proxy servers support WebSocket connections
4. CORS is properly configured for your domain

## Configuration Files

### config.toml
The main configuration file with WebSocket-friendly settings:
```toml
[core]
debug = true
runtime = "local"
enable_browser = true

[sandbox]
use_host_network = true
timeout = 120

[security]
confirmation_mode = false
```

### Frontend Environment
Create `.env` in the frontend directory:
```env
VITE_BACKEND_HOST=0.0.0.0:12000
VITE_FRONTEND_PORT=12001
VITE_USE_TLS=false
VITE_INSECURE_SKIP_VERIFY=true
```

## Production Deployment

For production environments:

1. **Use HTTPS/WSS**:
```env
VITE_USE_TLS=true
VITE_INSECURE_SKIP_VERIFY=false
```

2. **Configure proper CORS**:
```python
# In openhands/server/shared.py
sio = socketio.AsyncServer(
    cors_allowed_origins=['https://yourdomain.com']
)
```

3. **Use a reverse proxy** (nginx example):
```nginx
location /socket.io/ {
    proxy_pass http://backend:12000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## Testing WebSocket Connection

Use the built-in test page:
1. Start OpenHands with the startup script
2. Open browser developer console
3. Navigate to the frontend URL
4. Check Network tab -> WS for WebSocket connections
5. Verify events are being sent/received

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Enable debug mode and check logs
3. Verify your network configuration
4. Test with the provided startup script first

The WebSocket setup should work out of the box with the provided configuration. The startup script handles most common scenarios automatically.