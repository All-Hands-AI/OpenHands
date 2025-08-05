#!/bin/bash

# OpenHands Health Check Script
# Verifies that all services are running correctly

echo "🏥 OpenHands Health Check"
echo "========================"

# Check backend
echo "🔧 Checking backend (port 12000)..."
if curl -s http://localhost:12000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
    BACKEND_OK=true
else
    echo "❌ Backend is not responding"
    BACKEND_OK=false
fi

# Check frontend
echo "🎨 Checking frontend (port 12001)..."
if curl -s http://localhost:12001 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
    FRONTEND_OK=true
else
    echo "❌ Frontend is not responding"
    FRONTEND_OK=false
fi

# Check WebSocket
echo "🔌 Checking WebSocket connection..."
if command -v python3 > /dev/null; then
    if python3 test_websocket.py --host localhost --port 12000 > /dev/null 2>&1; then
        echo "✅ WebSocket is working"
        WEBSOCKET_OK=true
    else
        echo "❌ WebSocket connection failed"
        WEBSOCKET_OK=false
    fi
else
    echo "⚠️  Python3 not found, skipping WebSocket test"
    WEBSOCKET_OK=true
fi

# Summary
echo ""
echo "📊 Health Check Summary:"
echo "  Backend:   $([ "$BACKEND_OK" = true ] && echo "✅ OK" || echo "❌ FAIL")"
echo "  Frontend:  $([ "$FRONTEND_OK" = true ] && echo "✅ OK" || echo "❌ FAIL")"
echo "  WebSocket: $([ "$WEBSOCKET_OK" = true ] && echo "✅ OK" || echo "❌ FAIL")"

if [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ] && [ "$WEBSOCKET_OK" = true ]; then
    echo ""
    echo "🎉 All services are healthy!"
    echo ""
    echo "📡 Access URLs:"
    echo "  Frontend: https://work-2-bpecbsfrjhckrhbt.prod-runtime.all-hands.dev"
    echo "  Backend:  https://work-1-bpecbsfrjhckrhbt.prod-runtime.all-hands.dev"
    exit 0
else
    echo ""
    echo "❌ Some services are not healthy. Check the logs and configuration."
    exit 1
fi