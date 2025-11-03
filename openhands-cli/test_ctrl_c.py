#!/usr/bin/env python3
"""
Test script to verify Ctrl+C behavior in the OpenHands CLI.

This script simulates the signal handling behavior to test:
1. First Ctrl+C attempts graceful pause
2. Second Ctrl+C (within 3 seconds) kills process immediately
"""

import signal
import time
import multiprocessing
from openhands_cli.signal_handler import ProcessSignalHandler


def mock_conversation_process():
    """Mock conversation process that runs indefinitely"""
    print("Mock conversation process started...")
    try:
        while True:
            print("Agent is working...")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Mock conversation process received KeyboardInterrupt")
    except Exception as e:
        print(f"Mock conversation process error: {e}")
    finally:
        print("Mock conversation process ending")


def test_signal_handling():
    """Test the signal handling behavior"""
    print("Testing Ctrl+C signal handling...")
    print("Instructions:")
    print("1. Press Ctrl+C once - should attempt graceful pause")
    print("2. Press Ctrl+C again within 3 seconds - should kill immediately")
    print("3. Wait more than 3 seconds between presses to test timeout reset")
    print()
    
    # Create and start mock process
    process = multiprocessing.Process(target=mock_conversation_process)
    process.start()
    
    # Install signal handler
    signal_handler = ProcessSignalHandler()
    signal_handler.install_handler()
    signal_handler.set_conversation_process(process)
    
    try:
        print("Process started. Press Ctrl+C to test signal handling...")
        print("Process PID:", process.pid)
        
        # Wait for process to finish or be killed
        while process.is_alive():
            time.sleep(0.5)
            
        print(f"Process finished with exit code: {process.exitcode}")
        
    except KeyboardInterrupt:
        print("Main process received KeyboardInterrupt")
    finally:
        # Clean up
        signal_handler.uninstall_handler()
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join()
        print("Test completed")


if __name__ == "__main__":
    test_signal_handling()