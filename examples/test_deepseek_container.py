#!/usr/bin/env python3
"""
Test script for DeepSeek R1-0528 Docker container

This script performs basic validation of the container environment
without requiring the full model download.
"""

import sys
import torch
import time
import os
from typing import Dict, Any

def test_environment():
    """Test the container environment"""
    print("🧪 Testing DeepSeek Container Environment")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Python version
    print("1. Python Version:")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"   ✓ Python {python_version}")
    results["python_version"] = python_version
    
    # Test 2: PyTorch installation
    print("\n2. PyTorch Installation:")
    try:
        print(f"   ✓ PyTorch {torch.__version__}")
        results["pytorch_version"] = torch.__version__
        results["pytorch_available"] = True
    except Exception as e:
        print(f"   ✗ PyTorch error: {e}")
        results["pytorch_available"] = False
    
    # Test 3: CUDA availability
    print("\n3. CUDA Support:")
    if torch.cuda.is_available():
        print(f"   ✓ CUDA available: {torch.version.cuda}")
        print(f"   ✓ GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            gpu_name = torch.cuda.get_device_name(i)
            print(f"   ✓ GPU {i}: {gpu_name}")
        results["cuda_available"] = True
    else:
        print("   ⚠ CUDA not available (CPU mode)")
        results["cuda_available"] = False
    
    # Test 4: Required packages
    print("\n4. Required Packages:")
    required_packages = [
        "transformers",
        "accelerate", 
        "numpy",
        "torch"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {package}")
            results[f"{package}_available"] = True
        except ImportError:
            print(f"   ✗ {package} not found")
            results[f"{package}_available"] = False
    
    # Test 5: Environment variables
    print("\n5. Environment Variables:")
    env_vars = [
        "HF_HOME",
        "TRANSFORMERS_CACHE",
        "PYTHONUNBUFFERED"
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"   {var}: {value}")
        results[f"env_{var.lower()}"] = value
    
    # Test 6: File system
    print("\n6. File System:")
    important_paths = [
        "/app/examples",
        "/app/cache/huggingface",
        "/app/DEEPSEEK_R1_LOCAL_DEPLOYMENT_GUIDE.md"
    ]
    
    for path in important_paths:
        if os.path.exists(path):
            print(f"   ✓ {path}")
            results[f"path_{path.replace('/', '_').replace('.', '_')}"] = True
        else:
            print(f"   ✗ {path} not found")
            results[f"path_{path.replace('/', '_').replace('.', '_')}"] = False
    
    return results

def test_basic_torch_operations():
    """Test basic PyTorch operations"""
    print("\n🔧 Testing Basic PyTorch Operations")
    print("=" * 40)
    
    try:
        # Create a simple tensor
        x = torch.randn(3, 3)
        print(f"✓ Created tensor: {x.shape}")
        
        # Basic operations
        y = x + 1
        z = torch.matmul(x, y)
        print(f"✓ Matrix operations successful: {z.shape}")
        
        # Move to GPU if available
        if torch.cuda.is_available():
            x_gpu = x.cuda()
            print(f"✓ GPU tensor operations: {x_gpu.device}")
        
        return True
        
    except Exception as e:
        print(f"✗ PyTorch operations failed: {e}")
        return False

def test_transformers_import():
    """Test transformers library import"""
    print("\n🤖 Testing Transformers Library")
    print("=" * 35)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        print("✓ Transformers imports successful")
        
        # Test tokenizer creation (without downloading)
        print("✓ Transformers classes available")
        return True
        
    except Exception as e:
        print(f"✗ Transformers test failed: {e}")
        return False

def test_memory_info():
    """Test memory information"""
    print("\n💾 Memory Information")
    print("=" * 25)
    
    try:
        import psutil
        
        # System memory
        memory = psutil.virtual_memory()
        print(f"System Memory: {memory.total / 1e9:.2f} GB total")
        print(f"Available: {memory.available / 1e9:.2f} GB ({100 - memory.percent:.1f}%)")
        
        # GPU memory
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                total_memory = props.total_memory / 1e9
                print(f"GPU {i} Memory: {total_memory:.2f} GB")
        
        return True
        
    except Exception as e:
        print(f"✗ Memory info failed: {e}")
        return False

def generate_test_report(results: Dict[str, Any]):
    """Generate a test report"""
    print("\n📊 Test Report")
    print("=" * 20)
    
    # Count successes
    total_tests = len([k for k in results.keys() if k.endswith('_available') or k.startswith('path_')])
    passed_tests = len([k for k, v in results.items() if (k.endswith('_available') or k.startswith('path_')) and v is True])
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Environment summary
    print(f"\nEnvironment Summary:")
    print(f"- Python: {results.get('python_version', 'Unknown')}")
    print(f"- PyTorch: {results.get('pytorch_version', 'Not available')}")
    print(f"- CUDA: {'Available' if results.get('cuda_available') else 'Not available'}")
    
    # Recommendations
    print(f"\nRecommendations:")
    if not results.get('cuda_available'):
        print("- Consider using GPU-enabled environment for better performance")
    if passed_tests == total_tests:
        print("- ✅ Container is ready for DeepSeek R1-0528 deployment")
    else:
        print("- ⚠ Some components need attention before deployment")

def main():
    """Main test function"""
    print("🚀 DeepSeek R1-0528 Container Test Suite")
    print("=" * 50)
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    results = test_environment()
    torch_ok = test_basic_torch_operations()
    transformers_ok = test_transformers_import()
    memory_ok = test_memory_info()
    
    # Add test results
    results["torch_operations"] = torch_ok
    results["transformers_import"] = transformers_ok
    results["memory_info"] = memory_ok
    
    # Generate report
    generate_test_report(results)
    
    print(f"\n🏁 Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    if all([torch_ok, transformers_ok, memory_ok]):
        print("✅ All tests passed! Container is ready.")
        sys.exit(0)
    else:
        print("⚠ Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()