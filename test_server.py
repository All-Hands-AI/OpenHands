#!/usr/bin/env python3
"""
Test Web Server for DeepSeek R1-0528 Integration
Demonstrates the integrated fallback functionality with a simple web interface
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our integrated components
from openhands.core.config.llm_config import LLMConfig
from openhands.llm.enhanced_llm import EnhancedLLM
from openhands.llm.deepseek_r1 import create_deepseek_r1_llm, is_deepseek_r1_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "deepseek-r1-0528"
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False
    use_fallback: bool = True

class ChatResponse(BaseModel):
    response: str
    model_used: str
    generation_time: float
    tokens: Dict[str, int]
    fallback_used: bool = False

class TestServer:
    """Test server for DeepSeek integration"""
    
    def __init__(self):
        self.app = FastAPI(
            title="DeepSeek R1-0528 Test Server",
            description="Test server for integrated DeepSeek R1-0528 with fallback",
            version="1.0.0"
        )
        self.enhanced_llm: Optional[EnhancedLLM] = None
        self.setup_routes()
        self.setup_middleware()
    
    def setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize the LLM on startup"""
            await self.initialize_llm()
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """Serve the test interface"""
            return self.get_test_interface()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            if not self.enhanced_llm:
                raise HTTPException(status_code=503, detail="LLM not initialized")
            
            return {
                "status": "healthy",
                "timestamp": int(time.time()),
                "fallback_enabled": self.enhanced_llm.is_fallback_enabled(),
                "fallback_status": self.enhanced_llm.get_fallback_status()
            }
        
        @self.app.post("/chat", response_model=ChatResponse)
        async def chat_completion(request: ChatRequest):
            """Chat completion endpoint"""
            if not self.enhanced_llm:
                raise HTTPException(status_code=503, detail="LLM not initialized")
            
            try:
                start_time = time.time()
                
                # Convert messages to the expected format
                messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
                
                # Use the enhanced LLM with fallback
                if request.use_fallback and self.enhanced_llm.is_fallback_enabled():
                    # Use fallback-enabled completion
                    response = self.enhanced_llm.completion(
                        messages=messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    )
                else:
                    # Use primary LLM directly
                    response = self.enhanced_llm.primary_llm.completion(
                        messages=messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    )
                
                generation_time = time.time() - start_time
                
                # Extract response content
                if hasattr(response, 'choices') and response.choices:
                    content = response.choices[0].message.content
                    model_used = getattr(response, 'model', 'unknown')
                elif isinstance(response, dict):
                    content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    model_used = response.get('model', 'unknown')
                else:
                    content = str(response)
                    model_used = 'unknown'
                
                return ChatResponse(
                    response=content,
                    model_used=model_used,
                    generation_time=generation_time,
                    tokens={
                        "input": len(' '.join([msg.content for msg in request.messages]).split()),
                        "output": len(content.split())
                    },
                    fallback_used=request.use_fallback and self.enhanced_llm.is_fallback_enabled()
                )
                
            except Exception as e:
                logger.error(f"Chat completion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models")
        async def list_models():
            """List available models"""
            models = ["deepseek-r1-0528"]
            
            # Add fallback models if available
            if self.enhanced_llm and self.enhanced_llm.fallback_manager:
                fallback_status = self.enhanced_llm.get_fallback_status()
                for provider_id in fallback_status.keys():
                    if provider_id not in models:
                        models.append(provider_id)
            
            return {
                "models": models,
                "primary": "deepseek-r1-0528",
                "fallback_enabled": self.enhanced_llm.is_fallback_enabled() if self.enhanced_llm else False
            }
        
        @self.app.get("/test")
        async def run_test():
            """Run a simple test of the integration"""
            if not self.enhanced_llm:
                raise HTTPException(status_code=503, detail="LLM not initialized")
            
            test_messages = [
                {"role": "user", "content": "Write a simple Python function to add two numbers."}
            ]
            
            try:
                start_time = time.time()
                
                # Test with fallback enabled
                response = self.enhanced_llm.completion(
                    messages=test_messages,
                    max_tokens=200,
                    temperature=0.7
                )
                
                generation_time = time.time() - start_time
                
                return {
                    "test_status": "success",
                    "response_preview": str(response)[:200] + "..." if len(str(response)) > 200 else str(response),
                    "generation_time": generation_time,
                    "fallback_status": self.enhanced_llm.get_fallback_status(),
                    "fallback_enabled": self.enhanced_llm.is_fallback_enabled()
                }
                
            except Exception as e:
                logger.error(f"Test failed: {e}")
                return {
                    "test_status": "failed",
                    "error": str(e),
                    "fallback_status": self.enhanced_llm.get_fallback_status() if self.enhanced_llm else {}
                }
    
    async def initialize_llm(self):
        """Initialize the Enhanced LLM with DeepSeek integration"""
        try:
            logger.info("Initializing Enhanced LLM with DeepSeek R1-0528...")
            
            # Create LLM config for DeepSeek R1-0528
            config = LLMConfig(
                model="deepseek-r1-0528",
                api_key="test-key",  # This would normally come from environment
                base_url=None,
                enable_fallback=True,
                fallback_models=["deepseek-r1-0528"],
                auto_fallback_on_error=True,
                fallback_api_keys={"deepseek-r1-0528": "test-key"}
            )
            
            # Initialize Enhanced LLM
            self.enhanced_llm = EnhancedLLM(
                config=config,
                enable_auto_fallback=True
            )
            
            logger.info("Enhanced LLM initialized successfully")
            logger.info(f"Fallback enabled: {self.enhanced_llm.is_fallback_enabled()}")
            logger.info(f"Fallback status: {self.enhanced_llm.get_fallback_status()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            # For demo purposes, we'll continue without the actual model
            logger.warning("Continuing in demo mode without actual model")
    
    def get_test_interface(self) -> str:
        """Generate HTML test interface"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek R1-0528 Test Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .status-panel {
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .chat-container {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        .input-panel {
            flex: 1;
        }
        .output-panel {
            flex: 1;
        }
        textarea {
            width: 100%;
            height: 200px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: monospace;
            resize: vertical;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        .response-box {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            min-height: 200px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .metrics {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .loading {
            opacity: 0.6;
        }
        .settings {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .settings label {
            display: inline-block;
            width: 120px;
            margin-right: 10px;
        }
        .settings input, .settings select {
            margin: 5px;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 DeepSeek R1-0528 Integration Test</h1>
        
        <div class="status-panel">
            <h3>System Status</h3>
            <div id="status">Loading...</div>
        </div>
        
        <div class="settings">
            <h3>Settings</h3>
            <label>Model:</label>
            <select id="model">
                <option value="deepseek-r1-0528">DeepSeek R1-0528</option>
            </select>
            <br>
            <label>Max Tokens:</label>
            <input type="number" id="maxTokens" value="512" min="1" max="2048">
            <br>
            <label>Temperature:</label>
            <input type="number" id="temperature" value="0.7" min="0" max="2" step="0.1">
            <br>
            <label>Use Fallback:</label>
            <input type="checkbox" id="useFallback" checked>
        </div>
        
        <div class="chat-container">
            <div class="input-panel">
                <h3>Input</h3>
                <textarea id="userInput" placeholder="Enter your message here...">Write a Python function to calculate the factorial of a number.</textarea>
                <br>
                <button onclick="sendMessage()" id="sendBtn">Send Message</button>
                <button onclick="runTest()">Run Test</button>
                <button onclick="checkHealth()">Check Health</button>
                <button onclick="clearOutput()">Clear</button>
            </div>
            
            <div class="output-panel">
                <h3>Response</h3>
                <div id="response" class="response-box">Response will appear here...</div>
                <div id="metrics" class="metrics" style="display: none;"></div>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <h3>Quick Tests</h3>
            <button onclick="testCodeGeneration()">Test Code Generation</button>
            <button onclick="testExplanation()">Test Explanation</button>
            <button onclick="testProblemSolving()">Test Problem Solving</button>
            <button onclick="testFallback()">Test Fallback</button>
        </div>
    </div>

    <script>
        let isLoading = false;

        async function checkHealth() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                document.getElementById('status').innerHTML = `
                    <strong>Status:</strong> ${data.status}<br>
                    <strong>Fallback Enabled:</strong> ${data.fallback_enabled}<br>
                    <strong>Timestamp:</strong> ${new Date(data.timestamp * 1000).toLocaleString()}<br>
                    <strong>Fallback Status:</strong> <pre>${JSON.stringify(data.fallback_status, null, 2)}</pre>
                `;
            } catch (error) {
                document.getElementById('status').innerHTML = `<span class="error">Error: ${error.message}</span>`;
            }
        }

        async function sendMessage() {
            if (isLoading) return;
            
            const userInput = document.getElementById('userInput').value;
            if (!userInput.trim()) {
                alert('Please enter a message');
                return;
            }
            
            setLoading(true);
            
            try {
                const requestData = {
                    messages: [
                        { role: "user", content: userInput }
                    ],
                    model: document.getElementById('model').value,
                    max_tokens: parseInt(document.getElementById('maxTokens').value),
                    temperature: parseFloat(document.getElementById('temperature').value),
                    use_fallback: document.getElementById('useFallback').checked
                };
                
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                document.getElementById('response').textContent = data.response;
                document.getElementById('metrics').innerHTML = `
                    <strong>Model Used:</strong> ${data.model_used}<br>
                    <strong>Generation Time:</strong> ${data.generation_time.toFixed(2)}s<br>
                    <strong>Input Tokens:</strong> ${data.tokens.input}<br>
                    <strong>Output Tokens:</strong> ${data.tokens.output}<br>
                    <strong>Fallback Used:</strong> ${data.fallback_used}
                `;
                document.getElementById('metrics').style.display = 'block';
                
            } catch (error) {
                document.getElementById('response').innerHTML = `<span class="error">Error: ${error.message}</span>`;
                document.getElementById('metrics').style.display = 'none';
            }
            
            setLoading(false);
        }

        async function runTest() {
            if (isLoading) return;
            
            setLoading(true);
            
            try {
                const response = await fetch('/test');
                const data = await response.json();
                
                document.getElementById('response').innerHTML = `
                    <strong>Test Status:</strong> ${data.test_status}<br><br>
                    <strong>Response Preview:</strong><br>
                    ${data.response_preview || data.error}<br><br>
                    <strong>Generation Time:</strong> ${data.generation_time || 'N/A'}<br>
                    <strong>Fallback Enabled:</strong> ${data.fallback_enabled}<br>
                    <strong>Fallback Status:</strong><br>
                    <pre>${JSON.stringify(data.fallback_status, null, 2)}</pre>
                `;
                
            } catch (error) {
                document.getElementById('response').innerHTML = `<span class="error">Test Error: ${error.message}</span>`;
            }
            
            setLoading(false);
        }

        function testCodeGeneration() {
            document.getElementById('userInput').value = "Write a Python function to implement binary search on a sorted array.";
            sendMessage();
        }

        function testExplanation() {
            document.getElementById('userInput').value = "Explain the concept of machine learning and its main types.";
            sendMessage();
        }

        function testProblemSolving() {
            document.getElementById('userInput').value = "How would you optimize a slow database query? Provide specific techniques.";
            sendMessage();
        }

        function testFallback() {
            document.getElementById('userInput').value = "Test the fallback mechanism by generating a response.";
            document.getElementById('useFallback').checked = true;
            sendMessage();
        }

        function clearOutput() {
            document.getElementById('response').textContent = 'Response will appear here...';
            document.getElementById('metrics').style.display = 'none';
        }

        function setLoading(loading) {
            isLoading = loading;
            const sendBtn = document.getElementById('sendBtn');
            const container = document.querySelector('.container');
            
            if (loading) {
                sendBtn.textContent = 'Generating...';
                sendBtn.disabled = true;
                container.classList.add('loading');
            } else {
                sendBtn.textContent = 'Send Message';
                sendBtn.disabled = false;
                container.classList.remove('loading');
            }
        }

        // Initialize
        window.onload = function() {
            checkHealth();
        };
    </script>
</body>
</html>
        """

def main():
    """Main function to run the test server"""
    server = TestServer()
    
    # Configure uvicorn
    config = uvicorn.Config(
        app=server.app,
        host="0.0.0.0",
        port=12000,  # Use the available port from runtime info
        log_level="info",
        reload=False
    )
    
    # Start server
    server_instance = uvicorn.Server(config)
    
    print("=" * 60)
    print("🚀 DeepSeek R1-0528 Integration Test Server")
    print("=" * 60)
    print(f"🌐 Server starting at: http://0.0.0.0:12000")
    print(f"🌐 External access: https://work-1-mscsekbcievybxrw.prod-runtime.all-hands.dev")
    print("📋 Available endpoints:")
    print("   - /          : Web interface")
    print("   - /health    : Health check")
    print("   - /chat      : Chat completion API")
    print("   - /test      : Run integration test")
    print("   - /models    : List available models")
    print("=" * 60)
    
    try:
        server_instance.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()