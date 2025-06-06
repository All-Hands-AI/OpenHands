#!/usr/bin/env python3
"""
Local DeepSeek R1-0528 Mock Server

This script provides a mock API server that simulates DeepSeek R1-0528
responses without requiring GPU or complex dependencies.
Perfect for development and testing when full vLLM setup is not available.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import random

# FastAPI app setup
app = FastAPI(title="Local DeepSeek R1-0528 Mock Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str

# Mock DeepSeek R1-0528 responses for different types of requests
CODING_RESPONSES = [
    "I'll help you implement this code solution. Let me break it down step by step and provide a clean, efficient implementation.",
    "Based on your requirements, I can create a robust solution that follows best practices and includes proper error handling.",
    "I'll analyze your code request and provide a comprehensive implementation with detailed explanations.",
    "Let me implement this functionality for you with proper documentation and testing considerations.",
    "I can help you build this feature using modern programming practices and clean code principles."
]

DEBUGGING_RESPONSES = [
    "I can help you debug this issue. Let me analyze the problem and provide potential solutions with explanations.",
    "Looking at your error, I can identify several possible causes and provide step-by-step debugging approaches.",
    "I'll help you troubleshoot this problem by examining the code flow and identifying potential issues.",
    "Let me analyze this bug and provide you with both immediate fixes and preventive measures.",
    "I can assist with debugging by breaking down the problem and providing systematic solutions."
]

EXPLANATION_RESPONSES = [
    "I'll explain this concept clearly with examples and practical applications to help you understand.",
    "Let me break down this topic step by step, providing context and real-world examples.",
    "I can explain this in detail, covering the fundamentals and advanced aspects with clear examples.",
    "I'll provide a comprehensive explanation that covers both theory and practical implementation.",
    "Let me clarify this concept by explaining it from different angles with relevant examples."
]

GENERAL_RESPONSES = [
    "I'm here to help you with your request. Let me provide a thoughtful and comprehensive response.",
    "I can assist you with this task. Let me analyze your requirements and provide a detailed solution.",
    "I'll help you tackle this challenge by providing structured guidance and practical advice.",
    "Let me work on your request systematically to ensure we achieve the best possible outcome.",
    "I can provide assistance with this topic by offering detailed insights and actionable recommendations."
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Local DeepSeek R1-0528 Mock Server",
        "version": "1.0.0",
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "status": "running",
        "description": "Mock server simulating DeepSeek R1-0528 API responses"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "server_type": "mock"
    }

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            ModelInfo(
                id="deepseek-ai/DeepSeek-R1-0528",
                created=int(time.time()),
                owned_by="deepseek-ai"
            ).dict()
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Chat completions endpoint compatible with OpenAI API"""
    
    # Validate model
    if request.model not in ["deepseek-ai/DeepSeek-R1-0528", "DeepSeek-R1-0528"]:
        raise HTTPException(status_code=400, detail=f"Model {request.model} not found")
    
    # Get the last user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    last_message = user_messages[-1].content.lower()
    
    # Generate contextual response based on message content
    if any(keyword in last_message for keyword in ["code", "implement", "function", "class", "script", "program"]):
        response_pool = CODING_RESPONSES
        context = "coding"
    elif any(keyword in last_message for keyword in ["debug", "error", "bug", "fix", "issue", "problem"]):
        response_pool = DEBUGGING_RESPONSES
        context = "debugging"
    elif any(keyword in last_message for keyword in ["explain", "how", "what", "why", "describe", "clarify"]):
        response_pool = EXPLANATION_RESPONSES
        context = "explanation"
    else:
        response_pool = GENERAL_RESPONSES
        context = "general"
    
    # Select a response and customize it
    base_response = random.choice(response_pool)
    
    # Add context-specific details
    if context == "coding":
        response_text = f"{base_response}\n\nFor your specific request, I would recommend:\n1. Planning the architecture carefully\n2. Writing clean, maintainable code\n3. Including proper error handling\n4. Adding comprehensive tests\n5. Documenting the implementation"
    elif context == "debugging":
        response_text = f"{base_response}\n\nDebugging approach:\n1. Reproduce the issue consistently\n2. Check logs and error messages\n3. Use debugging tools and breakpoints\n4. Test with minimal examples\n5. Verify the fix thoroughly"
    elif context == "explanation":
        response_text = f"{base_response}\n\nKey points to understand:\n1. Core concepts and principles\n2. Practical applications\n3. Common use cases\n4. Best practices\n5. Potential pitfalls to avoid"
    else:
        response_text = f"{base_response}\n\nI'm ready to help you with whatever you need. Feel free to ask follow-up questions for more specific guidance."
    
    # Create response
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created_time = int(time.time())
    
    # Calculate token usage (approximate)
    prompt_tokens = sum(len(msg.content.split()) for msg in request.messages)
    completion_tokens = len(response_text.split())
    
    response = ChatCompletionResponse(
        id=completion_id,
        created=created_time,
        model=request.model,
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ],
        usage={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    )
    
    return response.dict()

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get specific model information"""
    if model_id not in ["deepseek-ai/DeepSeek-R1-0528", "DeepSeek-R1-0528"]:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return ModelInfo(
        id=model_id,
        created=int(time.time()),
        owned_by="deepseek-ai"
    ).dict()

@app.post("/test")
async def test_endpoint():
    """Test endpoint for validation"""
    return {
        "status": "success",
        "message": "Local DeepSeek R1-0528 mock server is working correctly",
        "timestamp": datetime.now().isoformat(),
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "server_type": "mock",
        "capabilities": [
            "Chat completions",
            "Model information",
            "Health checks",
            "OpenAI API compatibility"
        ]
    }

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    return {
        "server_type": "mock",
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "uptime": "Running",
        "requests_served": "N/A (mock server)",
        "memory_usage": "Minimal",
        "gpu_usage": "None (CPU only)",
        "status": "healthy"
    }

if __name__ == "__main__":
    print("🤖 Local DeepSeek R1-0528 Mock Server")
    print("=" * 50)
    print("🚀 Starting server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔗 OpenAI-compatible API: http://localhost:8000/v1/chat/completions")
    print("📋 Models endpoint: http://localhost:8000/v1/models")
    print("💚 Health check: http://localhost:8000/health")
    print("🧪 Test endpoint: http://localhost:8000/test")
    print("📊 Stats endpoint: http://localhost:8000/stats")
    print("=" * 50)
    print("✨ No GPU required - Pure CPU mock server")
    print("🔑 No API keys needed - Completely local")
    print("🎯 Perfect for development and testing")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )