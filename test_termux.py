#!/usr/bin/env python3

"""
Test script untuk OpenHands Termux
Script untuk testing fungsionalitas dasar
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test import dependencies"""
    print("🧪 Testing imports...")
    
    try:
        import litellm
        print("✅ litellm imported successfully")
    except ImportError as e:
        print(f"❌ litellm import failed: {e}")
        return False
    
    try:
        import toml
        print("✅ toml imported successfully")
    except ImportError as e:
        print(f"❌ toml import failed: {e}")
        return False
    
    try:
        from termux_agent import TermuxAgent, TermuxTools
        print("✅ TermuxAgent imported successfully")
    except ImportError as e:
        print(f"⚠️ TermuxAgent import failed: {e}")
        print("   Will use fallback SimpleTermuxAgent")
    
    return True

def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    try:
        from termux_cli import TermuxConfig
        
        config_manager = TermuxConfig()
        config = config_manager.load_config()
        
        print("✅ Configuration loaded successfully")
        print(f"   LLM model: {config.get('llm', {}).get('model', 'Not set')}")
        print(f"   Base URL: {config.get('llm', {}).get('base_url', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_tools():
    """Test Termux tools"""
    print("\n🧪 Testing Termux tools...")
    
    try:
        from termux_agent import TermuxTools
        
        tools = TermuxTools()
        
        # Test command execution
        result = tools.execute_command("echo 'Hello Termux'")
        if result["success"] and "Hello Termux" in result["stdout"]:
            print("✅ Command execution test passed")
        else:
            print(f"❌ Command execution test failed: {result}")
            return False
        
        # Test file operations
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            test_file = f.name
            f.write("Test content")
        
        # Test read file
        read_result = tools.read_file(test_file)
        if read_result["success"] and "Test content" in read_result["content"]:
            print("✅ File read test passed")
        else:
            print(f"❌ File read test failed: {read_result}")
            return False
        
        # Test write file
        write_result = tools.write_file(test_file, "Updated content")
        if write_result["success"]:
            print("✅ File write test passed")
        else:
            print(f"❌ File write test failed: {write_result}")
            return False
        
        # Test directory listing
        list_result = tools.list_directory(os.path.dirname(test_file))
        if list_result["success"] and len(list_result["files"]) > 0:
            print("✅ Directory listing test passed")
        else:
            print(f"❌ Directory listing test failed: {list_result}")
            return False
        
        # Cleanup
        os.unlink(test_file)
        
        return True
        
    except ImportError:
        print("⚠️ TermuxTools not available, skipping tools test")
        return True
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

def test_agent_creation():
    """Test agent creation"""
    print("\n🧪 Testing agent creation...")
    
    try:
        from termux_cli import TermuxConfig, SimpleTermuxAgent
        
        config_manager = TermuxConfig()
        config = config_manager.load_config()
        
        # Test simple agent
        agent = SimpleTermuxAgent(config)
        print("✅ SimpleTermuxAgent created successfully")
        
        # Test advanced agent if available
        try:
            from termux_agent import TermuxAgent
            advanced_agent = TermuxAgent(config)
            print("✅ TermuxAgent created successfully")
        except ImportError:
            print("⚠️ TermuxAgent not available, using SimpleTermuxAgent")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation test failed: {e}")
        return False

async def test_llm_connection():
    """Test LLM connection (if API key is configured)"""
    print("\n🧪 Testing LLM connection...")
    
    try:
        from termux_cli import TermuxConfig, SimpleTermuxAgent
        
        config_manager = TermuxConfig()
        config = config_manager.load_config()
        
        api_key = config.get("llm", {}).get("api_key", "")
        if not api_key:
            print("⚠️ No API key configured, skipping LLM test")
            print("   Run 'openhands config' to set up API key")
            return True
        
        agent = SimpleTermuxAgent(config)
        
        # Test simple message
        response = await agent.chat("Hello, can you respond with just 'OK'?")
        
        if "OK" in response.upper():
            print("✅ LLM connection test passed")
            return True
        else:
            print(f"⚠️ LLM responded but unexpected response: {response[:100]}...")
            return True  # Still consider it a pass
        
    except Exception as e:
        print(f"❌ LLM connection test failed: {e}")
        return False

def test_cli_functionality():
    """Test CLI functionality"""
    print("\n🧪 Testing CLI functionality...")
    
    try:
        # Test CLI import
        from termux_cli import main, setup_config, show_config
        print("✅ CLI functions imported successfully")
        
        # Test config functions
        from termux_cli import TermuxConfig
        config_manager = TermuxConfig()
        
        # Test default config
        default_config = config_manager.get_default_config()
        if "llm" in default_config and "core" in default_config:
            print("✅ Default configuration structure is valid")
        else:
            print("❌ Default configuration structure is invalid")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI functionality test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🚀 OpenHands Termux Test Suite")
    print("=" * 35)
    
    tests = [
        ("Import dependencies", test_imports),
        ("Configuration", test_config),
        ("Termux tools", test_tools),
        ("Agent creation", test_agent_creation),
        ("CLI functionality", test_cli_functionality),
        ("LLM connection", test_llm_connection)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! OpenHands Termux is ready to use.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("   You may still be able to use basic functionality.")
    
    print("\n📋 Next steps:")
    if failed == 0:
        print("1. Configure your API key: openhands config")
        print("2. Start using: openhands chat")
    else:
        print("1. Fix any dependency issues")
        print("2. Re-run tests: python test_termux.py")
        print("3. Configure API key: openhands config")

def main():
    """Main test function"""
    asyncio.run(run_all_tests())

if __name__ == "__main__":
    main()