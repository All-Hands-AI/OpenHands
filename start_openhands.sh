#!/bin/bash

# OpenHands WebSocket Configuration Startup Script
# This script properly configures and starts OpenHands with WebSocket support

set -e

echo "🚀 Starting OpenHands with WebSocket configuration..."

# Set environment variables for the runtime environment
export INSTALL_DOCKER=0
export RUNTIME=local
export BACKEND_HOST=0.0.0.0
export BACKEND_PORT=12000
export FRONTEND_HOST=0.0.0.0
export FRONTEND_PORT=12001
export SERVE_FRONTEND=true

# WebSocket specific configurations
export DEBUG=true
export CORS_ALLOWED_ORIGINS="*"

# Ensure the workspace directory exists
mkdir -p ./workspace

# Copy configuration templates if they don't exist
if [ ! -f config.toml ]; then
    echo "📋 Creating config.toml from template..."
    cp config.websocket.toml config.toml
fi

if [ ! -f frontend/.env ]; then
    echo "📋 Creating frontend/.env from template..."
    cp frontend/.env.websocket frontend/.env
fi

echo "📋 Configuration:"
echo "  Backend: ${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Frontend: ${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "  Runtime: ${RUNTIME}"
echo "  WebSocket: Enabled with CORS support"

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*openhands.server.listen" || true
pkill -f "npm.*dev" || true
sleep 2

# Start the backend server
echo "🔧 Starting backend server..."
poetry run uvicorn openhands.server.listen:app \
    --host ${BACKEND_HOST} \
    --port ${BACKEND_PORT} \
    --reload \
    --reload-exclude "./workspace" \
    --log-level debug &

BACKEND_PID=$!
echo "Backend started with PID: ${BACKEND_PID}"

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
timeout=30
while ! nc -z localhost ${BACKEND_PORT} && [ $timeout -gt 0 ]; do
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    echo "❌ Backend failed to start within 30 seconds"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Backend is ready!"

# Start the frontend server
echo "🎨 Starting frontend server..."
cd frontend

# Set frontend environment variables
export VITE_BACKEND_HOST="${BACKEND_HOST}:${BACKEND_PORT}"
export VITE_FRONTEND_PORT=${FRONTEND_PORT}
export VITE_USE_TLS=false
export VITE_INSECURE_SKIP_VERIFY=true

npm run dev -- --port ${FRONTEND_PORT} --host ${FRONTEND_HOST} &
FRONTEND_PID=$!
echo "Frontend started with PID: ${FRONTEND_PID}"

cd ..

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to start..."
timeout=30
while ! nc -z localhost ${FRONTEND_PORT} && [ $timeout -gt 0 ]; do
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    echo "❌ Frontend failed to start within 30 seconds"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Frontend is ready!"

echo ""
echo "🎉 OpenHands is now running!"
echo ""
echo "📡 Access URLs:"
echo "  Frontend: https://work-2-bpecbsfrjhckrhbt.prod-runtime.all-hands.dev"
echo "  Backend API: https://work-1-bpecbsfrjhckrhbt.prod-runtime.all-hands.dev"
echo ""
echo "🔌 WebSocket Configuration:"
echo "  - Socket.IO enabled with CORS support"
echo "  - Real-time communication between frontend and backend"
echo "  - Debug mode enabled for troubleshooting"
echo ""
echo "📝 To stop the servers:"
echo "  kill ${BACKEND_PID} ${FRONTEND_PID}"
echo ""
echo "📊 Monitoring logs:"
echo "  Backend logs: Check terminal output"
echo "  Frontend logs: Check browser developer console"

# Keep the script running and monitor the processes
trap 'echo "🛑 Shutting down..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0' INT TERM

# Monitor the processes
while kill -0 $BACKEND_PID 2>/dev/null && kill -0 $FRONTEND_PID 2>/dev/null; do
    sleep 5
done

echo "❌ One or more processes stopped unexpectedly"
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
exit 1