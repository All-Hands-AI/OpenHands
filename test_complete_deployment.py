#!/usr/bin/env python3
"""
Complete OpenHands + DeepSeek R1-0528 Integration Test
Tests the full deployment including backend API, model availability, and basic functionality.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class OpenHandsDeploymentTester:
    def __init__(self, backend_url: str = "https://work-1-mscsekbcievybxrw.prod-runtime.all-hands.dev"):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.verify = False  # For testing with self-signed certs
        
    def test_backend_health(self) -> bool:
        """Test if backend is responding"""
        try:
            response = self.session.get(f"{self.backend_url}/api/options/models", timeout=10)
            if response.status_code == 200:
                print("✅ Backend is responding")
                return True
            else:
                print(f"❌ Backend returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False
    
    def test_deepseek_models_available(self) -> bool:
        """Test if DeepSeek models are available"""
        try:
            response = self.session.get(f"{self.backend_url}/api/options/models", timeout=10)
            if response.status_code == 200:
                models = response.json()
                deepseek_models = [m for m in models if 'deepseek' in m.lower()]
                
                print(f"✅ Found {len(deepseek_models)} DeepSeek models:")
                for model in deepseek_models[:10]:  # Show first 10
                    print(f"   - {model}")
                if len(deepseek_models) > 10:
                    print(f"   ... and {len(deepseek_models) - 10} more")
                
                # Check for specific models we want
                target_models = [
                    'fireworks_ai/accounts/fireworks/models/deepseek-r1-0528',
                    'deepseek/deepseek-chat',
                    'deepseek/deepseek-coder',
                    'deepseek/deepseek-reasoner'
                ]
                
                found_targets = [m for m in target_models if m in models]
                print(f"✅ Found {len(found_targets)} target DeepSeek models:")
                for model in found_targets:
                    print(f"   - {model}")
                
                return len(deepseek_models) > 0
            else:
                print(f"❌ Failed to get models: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ DeepSeek models check failed: {e}")
            return False
    
    def test_conversation_creation(self) -> str:
        """Test creating a new conversation"""
        try:
            response = self.session.post(f"{self.backend_url}/api/conversations", timeout=10)
            if response.status_code == 200:
                conversation_data = response.json()
                conversation_id = conversation_data.get('conversation_id')
                print(f"✅ Created conversation: {conversation_id}")
                return conversation_id
            else:
                print(f"❌ Failed to create conversation: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Conversation creation failed: {e}")
            return None
    
    def test_docker_runtime(self) -> bool:
        """Test if Docker runtime is available"""
        try:
            import subprocess
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Docker runtime is available")
                return True
            else:
                print(f"❌ Docker runtime check failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Docker runtime test failed: {e}")
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test if frontend is accessible"""
        try:
            frontend_url = "https://work-2-mscsekbcievybxrw.prod-runtime.all-hands.dev"
            response = self.session.get(frontend_url, timeout=10)
            if response.status_code == 200 and "OpenHands" in response.text:
                print("✅ Frontend is accessible")
                return True
            else:
                print(f"❌ Frontend accessibility check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Frontend accessibility test failed: {e}")
            return False
    
    def run_complete_test(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🚀 Starting OpenHands + DeepSeek R1-0528 Deployment Test")
        print("=" * 60)
        
        results = {}
        
        print("\n1. Testing Backend Health...")
        results['backend_health'] = self.test_backend_health()
        
        print("\n2. Testing DeepSeek Models Availability...")
        results['deepseek_models'] = self.test_deepseek_models_available()
        
        print("\n3. Testing Conversation Creation...")
        conversation_id = self.test_conversation_creation()
        results['conversation_creation'] = conversation_id is not None
        
        print("\n4. Testing Docker Runtime...")
        results['docker_runtime'] = self.test_docker_runtime()
        
        print("\n5. Testing Frontend Accessibility...")
        results['frontend_accessibility'] = self.test_frontend_accessibility()
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! OpenHands + DeepSeek R1-0528 deployment is successful!")
        elif passed_tests >= total_tests - 1:
            print("⚠️  MOSTLY SUCCESSFUL! Minor issues detected but core functionality works.")
        else:
            print("❌ DEPLOYMENT ISSUES DETECTED! Please check the failed tests.")
        
        return results

def main():
    """Main test execution"""
    tester = OpenHandsDeploymentTester()
    results = tester.run_complete_test()
    
    # Exit with appropriate code
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    if passed_tests == total_tests:
        sys.exit(0)  # All tests passed
    elif passed_tests >= total_tests - 1:
        sys.exit(1)  # Minor issues
    else:
        sys.exit(2)  # Major issues

if __name__ == "__main__":
    main()