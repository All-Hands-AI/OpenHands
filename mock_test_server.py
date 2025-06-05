#!/usr/bin/env python3
"""
Mock Test Web Server for DeepSeek R1-0528 Integration
Demonstrates the integrated fallback functionality with simulated responses
"""

import asyncio
import json
import logging
import time
import random
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

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

class MockTestServer:
    """Mock test server for DeepSeek integration demonstration"""
    
    def __init__(self):
        self.app = FastAPI(
            title="DeepSeek R1-0528 Mock Test Server",
            description="Mock test server for integrated DeepSeek R1-0528 with fallback",
            version="1.0.0"
        )
        self.setup_routes()
        self.setup_middleware()
        
        # Mock state
        self.request_count = 0
        self.fallback_enabled = True
        self.primary_model_healthy = True
        self.fallback_models = ["deepseek-r1-0528", "gpt-3.5-turbo", "claude-3-haiku"]
        
        # Sample responses for different types of queries
        self.sample_responses = {
            "code": """def factorial(n):
    \"\"\"Calculate the factorial of a number.\"\"\"
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

# Example usage:
print(factorial(5))  # Output: 120""",
            
            "explanation": """Machine learning is a subset of artificial intelligence (AI) that enables computers to learn and make decisions from data without being explicitly programmed for every task.

Main types of machine learning:

1. **Supervised Learning**: Uses labeled data to train models
   - Examples: Classification, regression
   - Use cases: Email spam detection, price prediction

2. **Unsupervised Learning**: Finds patterns in unlabeled data
   - Examples: Clustering, dimensionality reduction
   - Use cases: Customer segmentation, anomaly detection

3. **Reinforcement Learning**: Learns through interaction and feedback
   - Examples: Game playing, robotics
   - Use cases: Autonomous vehicles, recommendation systems

The key advantage is that ML systems can improve their performance as they process more data, making them valuable for complex problems where traditional programming approaches fall short.""",
            
            "problem_solving": """To optimize a slow database query, here are specific techniques:

1. **Index Optimization**:
   - Add indexes on frequently queried columns
   - Use composite indexes for multi-column queries
   - Remove unused indexes to improve write performance

2. **Query Structure**:
   - Use EXPLAIN/EXPLAIN PLAN to analyze execution
   - Avoid SELECT * - specify only needed columns
   - Use appropriate JOIN types (INNER vs LEFT/RIGHT)

3. **Database Design**:
   - Normalize data to reduce redundancy
   - Consider denormalization for read-heavy workloads
   - Partition large tables by date or other criteria

4. **Caching Strategies**:
   - Implement query result caching
   - Use Redis or Memcached for frequently accessed data
   - Enable database query cache if available

5. **Hardware & Configuration**:
   - Increase memory allocation for buffer pools
   - Use SSDs for faster I/O operations
   - Tune database configuration parameters

6. **Application Level**:
   - Implement connection pooling
   - Use prepared statements to reduce parsing overhead
   - Consider read replicas for read-heavy applications""",
            
            "default": "I understand your request. As a DeepSeek R1-0528 model, I'm designed to provide helpful, accurate, and detailed responses. How can I assist you further with your specific question or task?"
        }
    
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
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            """Serve the test interface"""
            return self.get_test_interface()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": int(time.time()),
                "fallback_enabled": self.fallback_enabled,
                "fallback_status": {
                    "deepseek-r1-0528_primary": {
                        "is_healthy": self.primary_model_healthy,
                        "failure_count": 0 if self.primary_model_healthy else 2,
                        "last_success_time": int(time.time()) - (0 if self.primary_model_healthy else 300)
                    },
                    "gpt-3.5-turbo_fallback": {
                        "is_healthy": True,
                        "failure_count": 0,
                        "last_success_time": int(time.time())
                    }
                },
                "request_count": self.request_count,
                "mode": "mock_demo"
            }
        
        @self.app.post("/chat", response_model=ChatResponse)
        async def chat_completion(request: ChatRequest):
            """Chat completion endpoint with mock responses"""
            self.request_count += 1
            
            # Simulate processing time
            processing_time = random.uniform(0.5, 2.0)
            await asyncio.sleep(processing_time)
            
            try:
                # Determine which model to use
                model_used = request.model
                fallback_used = False
                
                # Simulate fallback logic
                if request.use_fallback and random.random() < 0.3:  # 30% chance of fallback
                    model_used = random.choice(self.fallback_models[1:])  # Use fallback model
                    fallback_used = True
                    self.primary_model_healthy = False
                else:
                    self.primary_model_healthy = True
                
                # Generate response based on content
                user_message = request.messages[-1].content.lower()
                
                if any(keyword in user_message for keyword in ["function", "code", "python", "programming", "algorithm"]):
                    response_text = self.sample_responses["code"]
                elif any(keyword in user_message for keyword in ["explain", "what is", "concept", "definition"]):
                    response_text = self.sample_responses["explanation"]
                elif any(keyword in user_message for keyword in ["optimize", "improve", "problem", "solve", "performance"]):
                    response_text = self.sample_responses["problem_solving"]
                else:
                    response_text = self.sample_responses["default"]
                
                # Add model-specific prefix
                if "deepseek" in model_used.lower():
                    prefix = "[DeepSeek R1-0528] "
                elif "gpt" in model_used.lower():
                    prefix = "[GPT-3.5 Fallback] "
                elif "claude" in model_used.lower():
                    prefix = "[Claude Fallback] "
                else:
                    prefix = "[Unknown Model] "
                
                final_response = prefix + response_text
                
                # Calculate token counts (approximate)
                input_tokens = sum(len(msg.content.split()) for msg in request.messages)
                output_tokens = len(final_response.split())
                
                return ChatResponse(
                    response=final_response,
                    model_used=model_used,
                    generation_time=processing_time,
                    tokens={
                        "input": input_tokens,
                        "output": output_tokens
                    },
                    fallback_used=fallback_used
                )
                
            except Exception as e:
                logger.error(f"Chat completion failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models")
        async def list_models():
            """List available models"""
            return {
                "models": self.fallback_models,
                "primary": "deepseek-r1-0528",
                "fallback_enabled": self.fallback_enabled,
                "available_fallbacks": self.fallback_models[1:]
            }
        
        @self.app.get("/test")
        async def run_test():
            """Run a simple test of the integration"""
            try:
                # Simulate test execution
                await asyncio.sleep(1.0)
                
                test_result = {
                    "test_status": "success",
                    "response_preview": "[DeepSeek R1-0528] def add_numbers(a, b):\n    \"\"\"Add two numbers together.\"\"\"\n    return a + b\n\n# Example usage:\nresult = add_numbers(5, 3)\nprint(f\"5 + 3 = {result}\")  # Output: 5 + 3 = 8",
                    "generation_time": 1.2,
                    "fallback_status": {
                        "deepseek-r1-0528_primary": {
                            "is_healthy": self.primary_model_healthy,
                            "failure_count": 0,
                            "last_success_time": int(time.time())
                        },
                        "gpt-3.5-turbo_fallback": {
                            "is_healthy": True,
                            "failure_count": 0,
                            "last_success_time": int(time.time())
                        }
                    },
                    "fallback_enabled": self.fallback_enabled,
                    "mode": "mock_demo",
                    "integration_features": [
                        "✓ DeepSeek R1-0528 primary model",
                        "✓ Automatic fallback mechanism",
                        "✓ Health monitoring",
                        "✓ Cost optimization",
                        "✓ Performance tracking"
                    ]
                }
                
                return test_result
                
            except Exception as e:
                logger.error(f"Test failed: {e}")
                return {
                    "test_status": "failed",
                    "error": str(e),
                    "fallback_status": {}
                }
        
        @self.app.post("/simulate_failure")
        async def simulate_failure():
            """Simulate primary model failure for testing fallback"""
            self.primary_model_healthy = False
            return {
                "message": "Primary model failure simulated",
                "primary_healthy": self.primary_model_healthy,
                "fallback_will_activate": True
            }
        
        @self.app.post("/reset_health")
        async def reset_health():
            """Reset all models to healthy state"""
            self.primary_model_healthy = True
            return {
                "message": "All models reset to healthy state",
                "primary_healthy": self.primary_model_healthy
            }
        
        @self.app.get("/stats")
        async def get_stats():
            """Get server statistics"""
            return {
                "total_requests": self.request_count,
                "primary_model_healthy": self.primary_model_healthy,
                "fallback_enabled": self.fallback_enabled,
                "available_models": len(self.fallback_models),
                "uptime_seconds": int(time.time()) - getattr(self, 'start_time', int(time.time())),
                "mode": "mock_demo",
                "features": {
                    "deepseek_integration": True,
                    "fallback_mechanism": True,
                    "health_monitoring": True,
                    "cost_optimization": True,
                    "performance_tracking": True
                }
            }
    
    def get_test_interface(self) -> str:
        """Generate HTML test interface"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek R1-0528 Integration Test</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-style: italic;
        }
        .status-panel {
            background: linear-gradient(135deg, #e8f4fd 0%, #d4edda 100%);
            border: 1px solid #bee5eb;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .demo-notice {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
        }
        .chat-container {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        .input-panel, .output-panel {
            flex: 1;
        }
        textarea {
            width: 100%;
            height: 200px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-family: 'Consolas', 'Monaco', monospace;
            resize: vertical;
            font-size: 14px;
        }
        textarea:focus {
            border-color: #667eea;
            outline: none;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            margin: 5px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
        }
        .response-box {
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            padding: 20px;
            min-height: 200px;
            white-space: pre-wrap;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        .metrics {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 1px solid #c3e6cb;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            font-size: 0.9em;
        }
        .error {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .loading {
            opacity: 0.6;
        }
        .settings {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .settings label {
            display: inline-block;
            width: 140px;
            margin-right: 10px;
            font-weight: bold;
        }
        .settings input, .settings select {
            margin: 8px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .quick-tests {
            margin-top: 30px;
            text-align: center;
        }
        .quick-tests h3 {
            margin-bottom: 15px;
        }
        .feature-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .feature-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background-color: #28a745; }
        .status-unhealthy { background-color: #dc3545; }
        .status-warning { background-color: #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 DeepSeek R1-0528 Integration Test</h1>
        <p class="subtitle">Advanced LLM Integration with Intelligent Fallback System</p>
        
        <div class="demo-notice">
            🎭 <strong>DEMO MODE:</strong> This is a mock demonstration of the DeepSeek R1-0528 integration. 
            Responses are simulated to showcase the fallback mechanism and features.
        </div>
        
        <div class="status-panel">
            <h3>🔍 System Status</h3>
            <div id="status">Loading system status...</div>
        </div>
        
        <div class="settings">
            <h3>⚙️ Configuration</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                <div>
                    <label>Model:</label>
                    <select id="model">
                        <option value="deepseek-r1-0528">DeepSeek R1-0528</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="claude-3-haiku">Claude 3 Haiku</option>
                    </select>
                </div>
                <div>
                    <label>Max Tokens:</label>
                    <input type="number" id="maxTokens" value="512" min="1" max="2048">
                </div>
                <div>
                    <label>Temperature:</label>
                    <input type="number" id="temperature" value="0.7" min="0" max="2" step="0.1">
                </div>
                <div>
                    <label>Enable Fallback:</label>
                    <input type="checkbox" id="useFallback" checked>
                </div>
            </div>
        </div>
        
        <div class="chat-container">
            <div class="input-panel">
                <h3>📝 Input</h3>
                <textarea id="userInput" placeholder="Enter your message here...">Write a Python function to calculate the factorial of a number using recursion.</textarea>
                <br>
                <button onclick="sendMessage()" id="sendBtn">🚀 Send Message</button>
                <button onclick="runTest()">🧪 Run Integration Test</button>
                <button onclick="checkHealth()">❤️ Health Check</button>
                <button onclick="clearOutput()">🗑️ Clear</button>
            </div>
            
            <div class="output-panel">
                <h3>💬 Response</h3>
                <div id="response" class="response-box">Response will appear here...</div>
                <div id="metrics" class="metrics" style="display: none;"></div>
            </div>
        </div>
        
        <div class="quick-tests">
            <h3>🎯 Quick Test Scenarios</h3>
            <button onclick="testCodeGeneration()">💻 Code Generation</button>
            <button onclick="testExplanation()">📚 Explanation</button>
            <button onclick="testProblemSolving()">🔧 Problem Solving</button>
            <button onclick="testFallback()">🔄 Fallback Mechanism</button>
            <button onclick="simulateFailure()">⚠️ Simulate Failure</button>
            <button onclick="resetHealth()">🔄 Reset Health</button>
        </div>
        
        <div class="feature-list">
            <div class="feature-item">
                <h4>🎯 DeepSeek R1-0528 Integration</h4>
                <p>Primary model with advanced reasoning capabilities and cost-effective pricing.</p>
            </div>
            <div class="feature-item">
                <h4>🔄 Intelligent Fallback</h4>
                <p>Automatic switching to backup models when primary model fails or is unavailable.</p>
            </div>
            <div class="feature-item">
                <h4>❤️ Health Monitoring</h4>
                <p>Real-time tracking of model health and performance metrics.</p>
            </div>
            <div class="feature-item">
                <h4>💰 Cost Optimization</h4>
                <p>Smart routing to cost-effective models while maintaining quality.</p>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;
        let startTime = Date.now();

        async function checkHealth() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                let statusHtml = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                        <div>
                            <strong>🟢 System Status:</strong> ${data.status}<br>
                            <strong>📊 Total Requests:</strong> ${data.request_count}<br>
                            <strong>🔄 Fallback Enabled:</strong> ${data.fallback_enabled ? '✅ Yes' : '❌ No'}<br>
                            <strong>🎭 Mode:</strong> ${data.mode}
                        </div>
                        <div>
                            <strong>🕒 Last Updated:</strong> ${new Date(data.timestamp * 1000).toLocaleString()}<br>
                            <strong>⏱️ Uptime:</strong> ${Math.floor((Date.now() - startTime) / 1000)}s
                        </div>
                    </div>
                    <h4>🔍 Model Health Status:</h4>
                `;
                
                for (const [modelId, status] of Object.entries(data.fallback_status)) {
                    const indicator = status.is_healthy ? 'status-healthy' : 'status-unhealthy';
                    statusHtml += `
                        <div style="margin: 8px 0;">
                            <span class="status-indicator ${indicator}"></span>
                            <strong>${modelId}:</strong> 
                            ${status.is_healthy ? '✅ Healthy' : '❌ Unhealthy'} 
                            (Failures: ${status.failure_count})
                        </div>
                    `;
                }
                
                document.getElementById('status').innerHTML = statusHtml;
            } catch (error) {
                document.getElementById('status').innerHTML = `<span class="error">❌ Error: ${error.message}</span>`;
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
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                        <div><strong>🤖 Model Used:</strong> ${data.model_used}</div>
                        <div><strong>⏱️ Generation Time:</strong> ${data.generation_time.toFixed(2)}s</div>
                        <div><strong>📥 Input Tokens:</strong> ${data.tokens.input}</div>
                        <div><strong>📤 Output Tokens:</strong> ${data.tokens.output}</div>
                        <div><strong>🔄 Fallback Used:</strong> ${data.fallback_used ? '✅ Yes' : '❌ No'}</div>
                        <div><strong>💰 Est. Cost:</strong> $${(data.tokens.input * 0.000014 + data.tokens.output * 0.000028).toFixed(6)}</div>
                    </div>
                `;
                document.getElementById('metrics').style.display = 'block';
                
                // Auto-refresh health status
                setTimeout(checkHealth, 1000);
                
            } catch (error) {
                document.getElementById('response').innerHTML = `<span class="error">❌ Error: ${error.message}</span>`;
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
                
                let resultHtml = `
                    <strong>🧪 Test Status:</strong> ${data.test_status === 'success' ? '✅ SUCCESS' : '❌ FAILED'}<br><br>
                `;
                
                if (data.test_status === 'success') {
                    resultHtml += `
                        <strong>📝 Response Preview:</strong><br>
                        ${data.response_preview}<br><br>
                        <strong>⏱️ Generation Time:</strong> ${data.generation_time}s<br>
                        <strong>🔄 Fallback Enabled:</strong> ${data.fallback_enabled ? '✅ Yes' : '❌ No'}<br><br>
                        <strong>✨ Integration Features:</strong><br>
                    `;
                    
                    data.integration_features.forEach(feature => {
                        resultHtml += `${feature}<br>`;
                    });
                } else {
                    resultHtml += `<strong>❌ Error:</strong> ${data.error}`;
                }
                
                document.getElementById('response').innerHTML = resultHtml;
                
            } catch (error) {
                document.getElementById('response').innerHTML = `<span class="error">🧪 Test Error: ${error.message}</span>`;
            }
            
            setLoading(false);
        }

        function testCodeGeneration() {
            document.getElementById('userInput').value = "Write a Python function to implement binary search on a sorted array with detailed comments.";
            sendMessage();
        }

        function testExplanation() {
            document.getElementById('userInput').value = "Explain the concept of machine learning and its main types with examples.";
            sendMessage();
        }

        function testProblemSolving() {
            document.getElementById('userInput').value = "How would you optimize a slow database query? Provide specific techniques and best practices.";
            sendMessage();
        }

        function testFallback() {
            document.getElementById('userInput').value = "Test the fallback mechanism by generating a comprehensive response about AI safety.";
            document.getElementById('useFallback').checked = true;
            sendMessage();
        }

        async function simulateFailure() {
            try {
                const response = await fetch('/simulate_failure', { method: 'POST' });
                const data = await response.json();
                alert(`✅ ${data.message}\\nFallback will activate on next request.`);
                checkHealth();
            } catch (error) {
                alert(`❌ Error: ${error.message}`);
            }
        }

        async function resetHealth() {
            try {
                const response = await fetch('/reset_health', { method: 'POST' });
                const data = await response.json();
                alert(`✅ ${data.message}`);
                checkHealth();
            } catch (error) {
                alert(`❌ Error: ${error.message}`);
            }
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
                sendBtn.textContent = '⏳ Generating...';
                sendBtn.disabled = true;
                container.classList.add('loading');
            } else {
                sendBtn.textContent = '🚀 Send Message';
                sendBtn.disabled = false;
                container.classList.remove('loading');
            }
        }

        // Initialize
        window.onload = function() {
            checkHealth();
            
            // Auto-refresh health status every 30 seconds
            setInterval(checkHealth, 30000);
        };
    </script>
</body>
</html>
        """

def main():
    """Main function to run the mock test server"""
    server = MockTestServer()
    server.start_time = int(time.time())
    
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
    
    print("=" * 80)
    print("🚀 DeepSeek R1-0528 Integration Mock Test Server")
    print("=" * 80)
    print(f"🌐 Local Server: http://0.0.0.0:12000")
    print(f"🌐 External Access: https://work-1-mscsekbcievybxrw.prod-runtime.all-hands.dev")
    print("📋 Available endpoints:")
    print("   - /                    : Interactive web interface")
    print("   - /health              : System health check")
    print("   - /chat                : Chat completion API")
    print("   - /test                : Integration test")
    print("   - /models              : List available models")
    print("   - /stats               : Server statistics")
    print("   - /simulate_failure    : Simulate primary model failure")
    print("   - /reset_health        : Reset all models to healthy state")
    print("")
    print("🎭 DEMO MODE: This server simulates DeepSeek R1-0528 responses")
    print("✨ Features demonstrated:")
    print("   - DeepSeek R1-0528 integration")
    print("   - Intelligent fallback mechanism")
    print("   - Health monitoring and recovery")
    print("   - Cost optimization")
    print("   - Performance tracking")
    print("=" * 80)
    
    try:
        server_instance.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()