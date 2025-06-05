#!/usr/bin/env python3
"""
Production DeepSeek R1-0528 Local Server

This script creates a production-ready local server for DeepSeek R1-0528
using transformers library with CPU/GPU optimization and OpenAI-compatible API.
"""

import os
import json
import time
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse
import signal
import sys
from typing import Dict, Any, Optional, List
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekServer:
    """Production DeepSeek R1-0528 server"""
    
    def __init__(self, 
                 model_name: str = "deepseek-ai/DeepSeek-R1-0528",
                 host: str = "0.0.0.0",
                 port: int = 8000,
                 use_quantization: bool = True,
                 max_length: int = 2048):
        
        self.model_name = model_name
        self.host = host
        self.port = port
        self.use_quantization = use_quantization
        self.max_length = max_length
        
        self.model = None
        self.tokenizer = None
        self.device = None
        self.server = None
        self.is_ready = False
        
        # Statistics
        self.stats = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "total_tokens_generated": 0,
            "average_response_time": 0.0,
            "start_time": time.time()
        }
    
    def load_model(self):
        """Load the DeepSeek model and tokenizer"""
        logger.info(f"Loading DeepSeek R1-0528 model: {self.model_name}")
        
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            
            # Determine device
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info(f"Using GPU: {torch.cuda.get_device_name()}")
            else:
                self.device = "cpu"
                logger.info("Using CPU mode")
            
            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            logger.info("✅ Tokenizer loaded")
            
            # Configure model loading
            model_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
            }
            
            # Add quantization for memory efficiency
            if self.use_quantization and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                model_kwargs["quantization_config"] = quantization_config
                model_kwargs["device_map"] = "auto"
                logger.info("Using 4-bit quantization")
            else:
                model_kwargs["device_map"] = "auto" if self.device == "cuda" else None
            
            # Load model
            logger.info("Loading model (this may take several minutes)...")
            start_time = time.time()
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded in {load_time:.2f} seconds")
            
            # Move to device if not using device_map
            if model_kwargs.get("device_map") is None and self.device == "cuda":
                self.model = self.model.to(self.device)
            
            # Print memory usage
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1e9
                logger.info(f"GPU memory allocated: {allocated:.2f} GB")
            
            self.is_ready = True
            logger.info("🎉 DeepSeek R1-0528 server is ready!")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate_response(self, messages: List[Dict[str, str]], 
                         max_tokens: int = 256,
                         temperature: float = 0.7,
                         top_p: float = 0.9) -> Dict[str, Any]:
        """Generate response using the model"""
        
        if not self.is_ready:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        try:
            import torch
            
            # Format messages into a prompt
            prompt = self._format_messages(messages)
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_length - max_tokens
            )
            
            # Move to device
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True
                )
            
            # Decode response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = full_response[len(prompt):].strip()
            
            # Calculate metrics
            input_tokens = inputs['input_ids'].shape[1]
            output_tokens = outputs.shape[1] - input_tokens
            generation_time = time.time() - start_time
            
            # Update statistics
            self.stats["requests_successful"] += 1
            self.stats["total_tokens_generated"] += output_tokens
            self.stats["average_response_time"] = (
                (self.stats["average_response_time"] * (self.stats["requests_successful"] - 1) + generation_time) /
                self.stats["requests_successful"]
            )
            
            return {
                "content": generated_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "generation_time": generation_time
            }
            
        except Exception as e:
            self.stats["requests_failed"] += 1
            logger.error(f"Generation failed: {e}")
            raise
        
        finally:
            self.stats["requests_total"] += 1
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into a prompt"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get server health status"""
        uptime = time.time() - self.stats["start_time"]
        
        return {
            "status": "healthy" if self.is_ready else "loading",
            "model": self.model_name,
            "device": self.device,
            "uptime_seconds": uptime,
            "statistics": self.stats.copy()
        }

class DeepSeekRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for DeepSeek API"""
    
    def __init__(self, *args, deepseek_server=None, **kwargs):
        self.deepseek_server = deepseek_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/stats":
            self._handle_stats()
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/v1/chat/completions":
            self._handle_chat_completions()
        else:
            self._send_error(404, "Not Found")
    
    def _handle_health(self):
        """Handle health check"""
        try:
            health = self.deepseek_server.get_health_status()
            self._send_json_response(health)
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_stats(self):
        """Handle statistics request"""
        try:
            stats = self.deepseek_server.stats.copy()
            self._send_json_response(stats)
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_chat_completions(self):
        """Handle chat completions request"""
        try:
            # Read request data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode())
            
            # Extract parameters
            messages = request_data.get("messages", [])
            max_tokens = request_data.get("max_tokens", 256)
            temperature = request_data.get("temperature", 0.7)
            top_p = request_data.get("top_p", 0.9)
            
            if not messages:
                self._send_error(400, "Messages are required")
                return
            
            # Generate response
            result = self.deepseek_server.generate_response(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            # Format OpenAI-compatible response
            response = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": self.deepseek_server.model_name,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["content"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": result["input_tokens"],
                    "completion_tokens": result["output_tokens"],
                    "total_tokens": result["input_tokens"] + result["output_tokens"]
                }
            }
            
            self._send_json_response(response)
            
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            self._send_error(500, str(e))
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        error_response = {
            "error": {
                "message": message,
                "type": "server_error",
                "code": status_code
            }
        }
        self._send_json_response(error_response, status_code)
    
    def log_message(self, format, *args):
        """Custom logging"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def create_handler(deepseek_server):
    """Create request handler with server instance"""
    def handler(*args, **kwargs):
        return DeepSeekRequestHandler(*args, deepseek_server=deepseek_server, **kwargs)
    return handler

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="DeepSeek R1-0528 Local Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--model", default="deepseek-ai/DeepSeek-R1-0528", help="Model name")
    parser.add_argument("--no-quantization", action="store_true", help="Disable quantization")
    parser.add_argument("--max-length", type=int, default=2048, help="Maximum sequence length")
    
    args = parser.parse_args()
    
    # Create server
    deepseek_server = DeepSeekServer(
        model_name=args.model,
        host=args.host,
        port=args.port,
        use_quantization=not args.no_quantization,
        max_length=args.max_length
    )
    
    # Load model in background
    def load_model():
        try:
            deepseek_server.load_model()
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            sys.exit(1)
    
    model_thread = threading.Thread(target=load_model)
    model_thread.daemon = True
    model_thread.start()
    
    # Create HTTP server
    handler = create_handler(deepseek_server)
    httpd = HTTPServer((args.host, args.port), handler)
    deepseek_server.server = httpd
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        logger.info("Shutting down server...")
        httpd.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start server
    logger.info(f"🚀 Starting DeepSeek R1-0528 server on {args.host}:{args.port}")
    logger.info("Model loading in background...")
    logger.info(f"Health check: http://{args.host}:{args.port}/health")
    logger.info(f"API endpoint: http://{args.host}:{args.port}/v1/chat/completions")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

if __name__ == "__main__":
    main()