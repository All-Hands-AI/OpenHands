#!/usr/bin/env python3

"""
OpenHands Termux Web UI Server
Backend server untuk web interface OpenHands Termux
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import psutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from termux_agent import TermuxAgent, TermuxTools
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    print("⚠️ TermuxAgent not available, using fallback mode")

try:
    import litellm
    from litellm import completion
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️ LiteLLM not available, chat functionality disabled")

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    config: Dict[str, Any]
    api_key: str
    base_url: str

class CommandRequest(BaseModel):
    command: str

class FileReadRequest(BaseModel):
    path: str

class FileWriteRequest(BaseModel):
    path: str
    content: str

class ConfigTestRequest(BaseModel):
    api_key: str
    base_url: str
    model: str

# FastAPI app
app = FastAPI(
    title="OpenHands Termux API",
    description="Backend API for OpenHands Termux Web UI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
websocket_connections: Dict[str, WebSocket] = {}

# Tools instance
tools = TermuxTools() if AGENT_AVAILABLE else None

@app.get("/")
async def serve_index():
    """Serve the main index.html"""
    ui_dir = Path(__file__).parent / "termux_web_ui" / "dist"
    index_file = ui_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {"message": "OpenHands Termux API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_available": AGENT_AVAILABLE,
        "llm_available": LLM_AVAILABLE,
        "tools_available": tools is not None
    }

# Chat endpoints
@app.post("/api/chat")
async def chat_message(request: ChatRequest):
    """Send a chat message and get response"""
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM functionality not available")
    
    try:
        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": request.config.get("system_prompt", "You are a helpful AI assistant.")
            },
            {
                "role": "user",
                "content": request.message
            }
        ]
        
        # Call LLM with proper API key handling
        api_key = request.api_key if request.api_key != "unused" else None
        
        response = await completion(
            model=request.config.get("model", "gpt-3.5-turbo"),
            messages=messages,
            api_key=api_key,
            base_url=request.base_url,
            temperature=request.config.get("temperature", 0.7),
            max_tokens=request.config.get("max_tokens", 2048),
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response"""
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM functionality not available")
    
    async def generate():
        try:
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": request.config.get("system_prompt", "You are a helpful AI assistant.")
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ]
            
            # Stream response with proper API key handling
            api_key = request.api_key if request.api_key != "unused" else None
            
            response = await completion(
                model=request.config.get("model", "gpt-3.5-turbo"),
                messages=messages,
                api_key=api_key,
                base_url=request.base_url,
                temperature=request.config.get("temperature", 0.7),
                max_tokens=request.config.get("max_tokens", 2048),
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")

# System endpoints
@app.get("/api/system/info")
async def get_system_info():
    """Get system information"""
    try:
        # CPU info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory info
        memory = psutil.virtual_memory()
        
        # Disk info
        disk = psutil.disk_usage('/')
        
        # Network info
        try:
            network = psutil.net_io_counters()
            network_info = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
            }
        except:
            network_info = None
        
        # Battery info (Android specific)
        battery_info = None
        try:
            result = subprocess.run(['termux-battery-status'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                battery_info = json.loads(result.stdout)
        except:
            pass
        
        return {
            "cpu": {
                "count": cpu_count,
                "percent": cpu_percent
            },
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "available": memory.available,
                "percent": memory.percent,
                "free": memory.free
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "network": network_info,
            "battery": battery_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system/execute")
async def execute_command(request: CommandRequest):
    """Execute a system command"""
    try:
        if tools:
            result = tools.execute_command(request.command)
            return {
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "exitCode": result.get("returncode", 0)
            }
        else:
            # Fallback implementation
            result = subprocess.run(
                request.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exitCode": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File endpoints
@app.get("/api/files/read")
async def read_file(path: str):
    """Read a file"""
    try:
        if tools:
            result = tools.read_file(path)
            if result["success"]:
                return {"content": result["content"]}
            else:
                raise HTTPException(status_code=404, detail=result["error"])
        else:
            # Fallback implementation
            file_path = Path(path).expanduser()
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {"content": content}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/write")
async def write_file(request: FileWriteRequest):
    """Write a file"""
    try:
        if tools:
            result = tools.write_file(request.path, request.content)
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result["error"])
        else:
            # Fallback implementation
            file_path = Path(request.path).expanduser()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(request.content)
        
        return {"success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/list")
async def list_directory(path: str):
    """List directory contents"""
    try:
        if tools:
            result = tools.list_directory(path)
            if result["success"]:
                return {"files": result["files"]}
            else:
                raise HTTPException(status_code=404, detail=result["error"])
        else:
            # Fallback implementation
            dir_path = Path(path).expanduser()
            if not dir_path.exists():
                raise HTTPException(status_code=404, detail="Directory not found")
            
            files = []
            for item in dir_path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {"files": files}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Config endpoints
@app.post("/api/config/test")
async def test_config(request: ConfigTestRequest):
    """Test API configuration"""
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM functionality not available")
    
    try:
        # Test with a simple message
        api_key = request.api_key if request.api_key != "unused" else None
        
        response = await completion(
            model=request.model,
            messages=[{"role": "user", "content": "Hello"}],
            api_key=api_key,
            base_url=request.base_url,
            max_tokens=10
        )
        
        return {
            "success": True,
            "message": "Connection successful"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time communication"""
    await websocket.accept()
    connection_id = id(websocket)
    websocket_connections[connection_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "system_info":
                # Send system info
                try:
                    info = await get_system_info()
                    await websocket.send_text(json.dumps({
                        "type": "system_info",
                        "data": info
                    }))
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": str(e)
                    }))
            
    except WebSocketDisconnect:
        pass
    finally:
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]

# Serve static files
ui_dir = Path(__file__).parent / "termux_web_ui" / "dist"
if ui_dir.exists():
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="static")

def main():
    """Main function to run the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenHands Termux Web UI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--dev", action="store_true", help="Development mode")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting OpenHands Termux Web UI Server")
    print(f"📡 Server: http://{args.host}:{args.port}")
    print(f"🔧 Agent Available: {AGENT_AVAILABLE}")
    print(f"🤖 LLM Available: {LLM_AVAILABLE}")
    
    uvicorn.run(
        "termux_web_ui_server:app" if args.dev else app,
        host=args.host,
        port=args.port,
        reload=args.dev,
        access_log=args.dev
    )

if __name__ == "__main__":
    main()