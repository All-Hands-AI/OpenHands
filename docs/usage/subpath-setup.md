# Subpath Configuration

OpenHands can be configured to serve the application under a custom subpath instead of the root path. This is useful when you need to serve OpenHands behind a reverse proxy or as part of a larger application.

## Environment Variables

### `OPENHANDS_BASE_PATH`
- **Description**: Sets the base path where the OpenHands application will be served
- **Default**: `/` (root path)
- **Examples**: `/c3/c3openhands/`, `/ai-tools/openhands/`, `/my-subpath/`

### `VITE_APP_BASE_URL` (Frontend Only)
- **Description**: Sets the base URL for frontend assets during build time
- **Default**: `/`
- **Note**: This is automatically set when using Docker with `OPENHANDS_BASE_PATH`

## Docker Usage

### Basic Example
```bash
docker run -d \
  -e OPENHANDS_BASE_PATH="/c3/c3openhands/" \
  -p 3000:3000 \
  openhands/openhands:latest
```

The application will be available at: `http://localhost:3000/c3/c3openhands/`

### With Docker Compose
```yaml
version: '3.8'
services:
  openhands:
    image: openhands/openhands:latest
    environment:
      - OPENHANDS_BASE_PATH=/c3/c3openhands/
    ports:
      - "3000:3000"
```

### Behind a Reverse Proxy
When using a reverse proxy like nginx, configure both the proxy and OpenHands:

**nginx configuration:**
```nginx
location /c3/c3openhands/ {
    proxy_pass http://openhands:3000/c3/c3openhands/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

**OpenHands Docker container:**
```bash
docker run -d \
  -e OPENHANDS_BASE_PATH="/c3/c3openhands/" \
  openhands/openhands:latest
```

## Local Development

For local development, you can set the environment variable before starting the application:

```bash
export OPENHANDS_BASE_PATH="/c3/c3openhands/"
# Rebuild frontend with new base path
cd frontend
export VITE_APP_BASE_URL="/c3/c3openhands/"
npm run build:subpath
cd ..
# Start backend
make start-backend
```

## Important Notes

1. **Path Format**: Always include leading and trailing slashes (e.g., `/my-path/`, not `my-path`)
2. **Runtime Rebuild**: When using Docker, the frontend is automatically rebuilt at container startup if a custom base path is configured
3. **API Routes**: All API endpoints will be served under the configured subpath
4. **WebSocket**: WebSocket connections will also use the configured subpath
5. **Default Behavior**: If `OPENHANDS_BASE_PATH` is not set or is set to `/`, the application serves from the root path as usual

## Troubleshooting

### Assets Not Loading
If static assets (CSS, JS) are not loading properly:
1. Verify the `OPENHANDS_BASE_PATH` environment variable is set correctly
2. Ensure your reverse proxy is configured to pass through the correct paths
3. Check that the base path includes both leading and trailing slashes

### API Calls Failing
If API calls are failing:
1. Ensure the frontend and backend are using the same base path
2. Check that your reverse proxy is forwarding API routes correctly
3. Verify that WebSocket connections are properly configured for the subpath

### Container Rebuild Issues
If the frontend rebuild in Docker is failing:
1. Check that Node.js is available in the container
2. Verify that the frontend source code is properly copied to the container
3. Review container logs for specific build errors