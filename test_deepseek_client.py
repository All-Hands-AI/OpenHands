#!/usr/bin/env python3
"""
Test client for DeepSeek R1-0528 local server

This script tests the local DeepSeek server with various requests
to verify functionality and performance.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

class DeepSeekClient:
    """Client for testing DeepSeek local server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def wait_for_server(self, timeout: int = 300) -> bool:
        """Wait for server to be ready"""
        print(f"⏳ Waiting for server at {self.base_url}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    health = response.json()
                    if health.get("status") == "healthy":
                        print("✅ Server is ready!")
                        return True
                    else:
                        print(f"   Server status: {health.get('status', 'unknown')}")
                
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(5)
            elapsed = time.time() - start_time
            print(f"   Waiting... ({elapsed:.0f}s/{timeout}s)")
        
        print("❌ Server not ready within timeout")
        return False
    
    def get_health(self) -> Dict[str, Any]:
        """Get server health status"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        response = self.session.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]],
                       max_tokens: int = 256,
                       temperature: float = 0.7,
                       top_p: float = 0.9) -> Dict[str, Any]:
        """Send chat completion request"""
        
        data = {
            "model": "deepseek-ai/DeepSeek-R1-0528",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=60
        )
        
        response.raise_for_status()
        return response.json()
    
    def simple_chat(self, message: str, **kwargs) -> str:
        """Simple chat interface"""
        messages = [{"role": "user", "content": message}]
        response = self.chat_completion(messages, **kwargs)
        return response["choices"][0]["message"]["content"]

def test_basic_functionality(client: DeepSeekClient):
    """Test basic server functionality"""
    print("🧪 Testing Basic Functionality")
    print("=" * 30)
    
    try:
        # Test health check
        health = client.get_health()
        print(f"✅ Health check: {health['status']}")
        print(f"   Model: {health['model']}")
        print(f"   Device: {health['device']}")
        print(f"   Uptime: {health['uptime_seconds']:.1f}s")
        
        # Test simple chat
        print("\n📝 Testing simple chat...")
        response = client.simple_chat("What is the capital of France?", max_tokens=50)
        print(f"✅ Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_various_prompts(client: DeepSeekClient):
    """Test various types of prompts"""
    print("\n🎯 Testing Various Prompts")
    print("=" * 27)
    
    test_cases = [
        {
            "name": "Simple Question",
            "message": "What is 2 + 2?",
            "max_tokens": 30
        },
        {
            "name": "Code Generation",
            "message": "Write a Python function to calculate factorial:",
            "max_tokens": 150
        },
        {
            "name": "Explanation",
            "message": "Explain machine learning in simple terms:",
            "max_tokens": 100
        },
        {
            "name": "Creative Writing",
            "message": "Write a short poem about technology:",
            "max_tokens": 80
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n🔸 {test_case['name']}")
            print(f"   Prompt: {test_case['message']}")
            
            start_time = time.time()
            response = client.simple_chat(
                test_case['message'],
                max_tokens=test_case['max_tokens']
            )
            response_time = time.time() - start_time
            
            print(f"   Response ({response_time:.2f}s): {response[:100]}...")
            
            results.append({
                "name": test_case['name'],
                "success": True,
                "response_time": response_time,
                "response_length": len(response)
            })
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                "name": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n📊 Prompt Test Results: {successful}/{len(results)} successful")
    
    if successful > 0:
        avg_time = sum(r["response_time"] for r in results if r["success"]) / successful
        print(f"   Average response time: {avg_time:.2f}s")
    
    return successful == len(results)

def test_conversation(client: DeepSeekClient):
    """Test multi-turn conversation"""
    print("\n💬 Testing Multi-turn Conversation")
    print("=" * 33)
    
    try:
        # Multi-turn conversation
        messages = [
            {"role": "user", "content": "Hello! What's your name?"}
        ]
        
        # First turn
        response1 = client.chat_completion(messages, max_tokens=50)
        assistant_response1 = response1["choices"][0]["message"]["content"]
        print(f"User: {messages[0]['content']}")
        print(f"Assistant: {assistant_response1}")
        
        # Add to conversation
        messages.append({"role": "assistant", "content": assistant_response1})
        messages.append({"role": "user", "content": "Can you help me with Python programming?"})
        
        # Second turn
        response2 = client.chat_completion(messages, max_tokens=100)
        assistant_response2 = response2["choices"][0]["message"]["content"]
        print(f"User: {messages[2]['content']}")
        print(f"Assistant: {assistant_response2}")
        
        print("✅ Multi-turn conversation successful")
        return True
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False

def test_performance(client: DeepSeekClient):
    """Test server performance"""
    print("\n⚡ Testing Performance")
    print("=" * 19)
    
    try:
        # Get initial stats
        initial_stats = client.get_stats()
        print(f"Initial stats: {initial_stats['requests_total']} requests")
        
        # Run multiple requests
        test_message = "Count from 1 to 5:"
        num_requests = 3
        
        times = []
        for i in range(num_requests):
            start_time = time.time()
            response = client.simple_chat(test_message, max_tokens=30)
            response_time = time.time() - start_time
            times.append(response_time)
            print(f"   Request {i+1}: {response_time:.2f}s")
        
        # Get final stats
        final_stats = client.get_stats()
        
        # Calculate metrics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Performance Results:")
        print(f"   Requests: {num_requests}")
        print(f"   Average time: {avg_time:.2f}s")
        print(f"   Min time: {min_time:.2f}s")
        print(f"   Max time: {max_time:.2f}s")
        print(f"   Total requests processed: {final_stats['requests_total']}")
        print(f"   Success rate: {final_stats['requests_successful']}/{final_stats['requests_total']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def interactive_mode(client: DeepSeekClient):
    """Interactive chat mode"""
    print("\n💬 Interactive Mode")
    print("=" * 17)
    print("Type 'quit' to exit, 'stats' for statistics")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            elif user_input.lower() == 'stats':
                stats = client.get_stats()
                print(f"Server stats: {json.dumps(stats, indent=2)}")
                continue
            elif not user_input:
                continue
            
            print("DeepSeek: ", end="", flush=True)
            start_time = time.time()
            
            response = client.simple_chat(user_input, max_tokens=256)
            response_time = time.time() - start_time
            
            print(response)
            print(f"({response_time:.2f}s)")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")

def main():
    """Main test function"""
    print("🧪 DeepSeek R1-0528 Local Server Test")
    print("=" * 37)
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--skip-wait", action="store_true", help="Skip waiting for server")
    args = parser.parse_args()
    
    # Create client
    client = DeepSeekClient(args.url)
    
    try:
        # Wait for server (unless skipped)
        if not args.skip_wait:
            if not client.wait_for_server():
                print("❌ Server not available")
                return False
        
        # Run tests
        if args.interactive:
            interactive_mode(client)
            return True
        else:
            tests = [
                ("Basic Functionality", lambda: test_basic_functionality(client)),
                ("Various Prompts", lambda: test_various_prompts(client)),
                ("Conversation", lambda: test_conversation(client)),
                ("Performance", lambda: test_performance(client))
            ]
            
            results = []
            for test_name, test_func in tests:
                try:
                    result = test_func()
                    results.append((test_name, result))
                except Exception as e:
                    print(f"❌ {test_name} failed with exception: {e}")
                    results.append((test_name, False))
            
            # Summary
            print("\n📊 Test Summary")
            print("=" * 15)
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name}")
            
            print(f"\nResults: {passed}/{total} tests passed")
            
            if passed == total:
                print("\n🎉 All tests passed! Server is working correctly.")
                
                # Offer interactive mode
                if input("\nStart interactive mode? (y/N): ").lower().startswith('y'):
                    interactive_mode(client)
                
                return True
            else:
                print(f"\n⚠️  {total - passed} test(s) failed.")
                return False
    
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)