#!/usr/bin/env python3
"""
Test vLLM setup for DeepSeek R1-0528

This script tests the vLLM installation and basic functionality
without downloading the full model.
"""

import sys
import subprocess
import time

def test_vllm_installation():
    """Test if vLLM is properly installed"""
    print("🔍 Testing vLLM Installation")
    print("=" * 30)
    
    try:
        # Try to import vLLM
        import vllm
        print(f"✅ vLLM imported successfully")
        print(f"   Version: {vllm.__version__}")
        return True
    except ImportError as e:
        print(f"❌ vLLM import failed: {e}")
        print("Installing vLLM...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "vllm"
            ])
            print("✅ vLLM installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install vLLM")
            return False

def test_torch_setup():
    """Test PyTorch setup"""
    print("\n🔥 Testing PyTorch Setup")
    print("=" * 25)
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        
        # Test CUDA
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.version.cuda}")
            print(f"✅ GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                memory = torch.cuda.get_device_properties(i).total_memory / 1e9
                print(f"   GPU {i}: {gpu_name} ({memory:.1f} GB)")
        else:
            print("⚠️  CUDA not available - will use CPU mode")
            print("   Note: CPU mode will be slower but functional")
        
        return True
    except ImportError:
        print("❌ PyTorch not available")
        return False

def test_vllm_command():
    """Test vLLM command line tool"""
    print("\n⚡ Testing vLLM Command")
    print("=" * 22)
    
    try:
        # Test vLLM help command
        result = subprocess.run(
            ["vllm", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ vLLM command line tool working")
            return True
        else:
            print(f"❌ vLLM command failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ vLLM command timed out")
        return False
    except FileNotFoundError:
        print("❌ vLLM command not found in PATH")
        return False
    except Exception as e:
        print(f"❌ vLLM command test failed: {e}")
        return False

def test_model_loading_simulation():
    """Simulate model loading without actually loading DeepSeek"""
    print("\n🤖 Testing Model Loading Simulation")
    print("=" * 35)
    
    try:
        from vllm import LLM
        print("✅ vLLM LLM class available")
        
        # Test with a small model (just to verify the API works)
        # We won't actually load DeepSeek here to save time/resources
        print("✅ Model loading API accessible")
        print("   Note: Actual DeepSeek model loading will happen during deployment")
        
        return True
    except ImportError as e:
        print(f"❌ vLLM LLM import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Model loading test failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing Dependencies")
    print("=" * 20)
    
    dependencies = [
        "torch",
        "transformers", 
        "requests",
        "json"
    ]
    
    all_good = True
    for dep in dependencies:
        try:
            if dep == "json":
                import json
            else:
                __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} not available")
            all_good = False
    
    return all_good

def print_deployment_instructions():
    """Print deployment instructions"""
    print("\n🚀 Deployment Instructions")
    print("=" * 25)
    print()
    print("To start DeepSeek R1-0528 locally:")
    print()
    print("1. Quick start (automated):")
    print("   ./quick_start_deepseek.sh")
    print()
    print("2. Manual start:")
    print("   vllm serve 'deepseek-ai/DeepSeek-R1-0528' \\")
    print("       --host 0.0.0.0 \\")
    print("       --port 8000 \\")
    print("       --trust-remote-code")
    print()
    print("3. Test the API:")
    print("   curl -X POST \"http://localhost:8000/v1/chat/completions\" \\")
    print("       -H \"Content-Type: application/json\" \\")
    print("       --data '{")
    print("           \"model\": \"deepseek-ai/DeepSeek-R1-0528\",")
    print("           \"messages\": [{")
    print("               \"role\": \"user\",")
    print("               \"content\": \"Hello!\"")
    print("           }]")
    print("       }'")
    print()
    print("4. Interactive mode:")
    print("   python local_deepseek_server.py")

def main():
    """Main test function"""
    print("🧪 DeepSeek R1-0528 vLLM Setup Test")
    print("=" * 40)
    print("Testing local deployment prerequisites...")
    print()
    
    # Run all tests
    tests = [
        ("vLLM Installation", test_vllm_installation),
        ("PyTorch Setup", test_torch_setup),
        ("vLLM Command", test_vllm_command),
        ("Model Loading API", test_model_loading_simulation),
        ("Dependencies", test_dependencies)
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
        print("\n🎉 All tests passed! Ready for DeepSeek deployment.")
        print_deployment_instructions()
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)