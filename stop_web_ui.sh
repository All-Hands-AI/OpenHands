#!/bin/bash

# OpenHands Termux Web UI Stop Script
# Stops the web UI server and development server

echo "🛑 Stopping OpenHands Termux Web UI..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Stop FastAPI server (backend)
print_status "Stopping FastAPI backend server..."
FASTAPI_PID=$(pgrep -f "termux_web_ui_server.py" 2>/dev/null)
if [ ! -z "$FASTAPI_PID" ]; then
    kill $FASTAPI_PID 2>/dev/null
    sleep 2
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        print_success "FastAPI server stopped (PID: $FASTAPI_PID)"
    else
        print_warning "Force killing FastAPI server..."
        kill -9 $FASTAPI_PID 2>/dev/null
        print_success "FastAPI server force stopped"
    fi
else
    print_warning "FastAPI server not running"
fi

# Stop Vite development server (frontend)
print_status "Stopping Vite development server..."
VITE_PID=$(pgrep -f "vite.*termux_web_ui" 2>/dev/null)
if [ ! -z "$VITE_PID" ]; then
    kill $VITE_PID 2>/dev/null
    sleep 2
    if ! kill -0 $VITE_PID 2>/dev/null; then
        print_success "Vite development server stopped (PID: $VITE_PID)"
    else
        print_warning "Force killing Vite server..."
        kill -9 $VITE_PID 2>/dev/null
        print_success "Vite development server force stopped"
    fi
else
    print_warning "Vite development server not running"
fi

# Stop any Node.js processes related to the project
print_status "Stopping any remaining Node.js processes..."
NODE_PIDS=$(pgrep -f "node.*termux_web_ui" 2>/dev/null)
if [ ! -z "$NODE_PIDS" ]; then
    echo "$NODE_PIDS" | xargs kill 2>/dev/null
    sleep 1
    print_success "Node.js processes stopped"
else
    print_warning "No Node.js processes found"
fi

# Stop any Python processes related to uvicorn
print_status "Stopping uvicorn processes..."
UVICORN_PIDS=$(pgrep -f "uvicorn.*termux_web_ui_server" 2>/dev/null)
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "$UVICORN_PIDS" | xargs kill 2>/dev/null
    sleep 1
    print_success "Uvicorn processes stopped"
else
    print_warning "No uvicorn processes found"
fi

# Check if ports are still in use
print_status "Checking if ports are free..."

# Check port 8000 (backend)
if lsof -i :8000 >/dev/null 2>&1; then
    print_warning "Port 8000 still in use"
    PROC_8000=$(lsof -t -i :8000 2>/dev/null)
    if [ ! -z "$PROC_8000" ]; then
        print_status "Killing process on port 8000 (PID: $PROC_8000)"
        kill -9 $PROC_8000 2>/dev/null
    fi
else
    print_success "Port 8000 is free"
fi

# Check port 5173 (frontend dev server)
if lsof -i :5173 >/dev/null 2>&1; then
    print_warning "Port 5173 still in use"
    PROC_5173=$(lsof -t -i :5173 2>/dev/null)
    if [ ! -z "$PROC_5173" ]; then
        print_status "Killing process on port 5173 (PID: $PROC_5173)"
        kill -9 $PROC_5173 2>/dev/null
    fi
else
    print_success "Port 5173 is free"
fi

# Clean up any temporary files
print_status "Cleaning up temporary files..."
if [ -f "/tmp/termux_web_ui.pid" ]; then
    rm -f /tmp/termux_web_ui.pid
    print_success "Removed PID file"
fi

if [ -d "termux_web_ui/dist" ]; then
    print_status "Cleaning build directory..."
    rm -rf termux_web_ui/dist
    print_success "Build directory cleaned"
fi

# Final status check
echo ""
echo "🔍 Final Status Check"
echo "===================="

# Check if any related processes are still running
REMAINING_PROCS=$(pgrep -f "(termux_web_ui|uvicorn.*8000|vite.*5173)" 2>/dev/null || true)
if [ -z "$REMAINING_PROCS" ]; then
    print_success "All web UI processes stopped successfully"
else
    print_warning "Some processes may still be running:"
    ps aux | grep -E "(termux_web_ui|uvicorn.*8000|vite.*5173)" | grep -v grep || true
fi

# Check ports
if ! lsof -i :8000 >/dev/null 2>&1 && ! lsof -i :5173 >/dev/null 2>&1; then
    print_success "All ports are free"
else
    print_warning "Some ports may still be in use"
fi

echo ""
print_success "🎉 OpenHands Termux Web UI stopped!"
echo ""
echo "📋 To restart:"
echo "  ./start_web_ui.sh"
echo ""
echo "🔧 To check status:"
echo "  ./test_web_ui.sh"