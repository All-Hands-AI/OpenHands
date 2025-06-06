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
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        try:
            import torch
            print(f"✓ PyTorch {torch.__version__}")
            
            # Check CUDA
            if torch.cuda.is_available():
                print(f"✓ CUDA {torch.version.cuda}")
                print(f"✓ GPU: {torch.cuda.get_device_name()}")
            else:
                print("⚠ CUDA not available - using CPU mode")
            
            # Check vLLM
            try:
                import vllm
                print(f"✓ vLLM available")
                return True
            except ImportError:
                print("❌ vLLM not installed")
                print("Installing vLLM...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "vllm"])
                print("✓ vLLM installed")
                return True
                
        except Exception as e:
            print(f"❌ Dependency check failed: {e}")
            return False
    
    def install_dependencies(self):
        """Install required dependencies"""
        print("📦 Installing dependencies...")
        
        dependencies = [
            "vllm",
            "torch",
            "transformers>=4.37.0",
            "accelerate",
        ]
        
        for dep in dependencies:
            try:
                print(f"Installing {dep}...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", dep
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✓ {dep} installed")
            except subprocess.CalledProcessError:
                print(f"⚠ Failed to install {dep}")
    
    def start_server(self) -> bool:
        """Start the vLLM server"""
        print(f"🚀 Starting DeepSeek R1-0528 server...")
        print(f"Model: {self.model_name}")
        print(f"Host: {self.host}:{self.port}")
        
        # Build vLLM command
        cmd = [
            "vllm", "serve", self.model_name,
            "--host", self.host,
            "--port", str(self.port),
            "--gpu-memory-utilization", str(self.gpu_memory_utilization),
            "--trust-remote-code",
            "--max-model-len", "4096",
        ]
        
        # Add CPU-only flag if no CUDA
        try:
            import torch
            if not torch.cuda.is_available():
                cmd.extend(["--tensor-parallel-size", "1"])
        except:
            pass
        
        print(f"Command: {' '.join(cmd)}")
        
        try:
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                if self.is_server_ready():
                    print("✅ Server is ready!")
                    return True
                
                time.sleep(5)
                wait_time += 5
                print(f"   Waiting... ({wait_time}s/{max_wait}s)")
                
                # Check if process is still running
                if self.server_process.poll() is not None:
                    stdout, stderr = self.server_process.communicate()
                    print(f"❌ Server process died:")
                    print(f"STDOUT: {stdout}")
                    print(f"STDERR: {stderr}")
                    return False
            
            print("❌ Server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def is_server_ready(self) -> bool:
        """Check if server is ready to accept requests"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_server(self) -> bool:
        """Test the server with a simple request"""
        print("🧪 Testing server...")
        
        test_data = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": "What is the capital of France?"
                }
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"✅ Test successful!")
                print(f"Response: {content}")
                return True
            else:
                print(f"❌ Test failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def stop_server(self):
        """Stop the server"""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ Server stopped")
    
    def interactive_chat(self):
        """Interactive chat with the model"""
        print("\n💬 Interactive Chat Mode")
        print("=" * 30)
        print("Type 'quit' to exit")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                # Send request
                data = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ],
                    "max_tokens": 256,
                    "temperature": 0.7
                }
                
                print("DeepSeek: ", end="", flush=True)
                
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    print(content)
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nGoodbye!")

def main():
    """Main function"""
    print("🤖 DeepSeek R1-0528 Local Server")
    print("=" * 40)
    print("No API keys required - completely local!")
    print()
    
    # Create server instance
    server = LocalDeepSeekServer()
    
    try:
        # Check dependencies
        if not server.check_dependencies():
            print("Installing missing dependencies...")
            server.install_dependencies()
        
        # Start server
        if server.start_server():
            # Test server
            if server.test_server():
                print("\n🎉 Server is running successfully!")
                print(f"API endpoint: {server.base_url}/v1/chat/completions")
                print()
                print("Example curl command:")
                print(f"""curl -X POST "{server.base_url}/v1/chat/completions" \\
    -H "Content-Type: application/json" \\
    --data '{{
        "model": "{server.model_name}",
        "messages": [
            {{
                "role": "user",
                "content": "Hello, how are you?"
            }}
        ]
    }}'""")
                
                # Interactive chat
                server.interactive_chat()
            else:
                print("❌ Server test failed")
        else:
            print("❌ Failed to start server")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    
    finally:
        # Clean up
        server.stop_server()

if __name__ == "__main__":
    main()