#!/usr/bin/env python3

import sys
import traceback

print("=== Debug Import Test ===")

try:
    print("Step 1: Import the module...")
    import openhands.server.websocket.logging as logging_module
    print(f"Module loaded from: {logging_module.__file__}")

    print("Step 2: Check module contents...")
    contents = [name for name in dir(logging_module) if not name.startswith('_')]
    print(f"Module contents: {contents}")

    print("Step 3: Try to access CorrelationIdManager...")
    if hasattr(logging_module, 'CorrelationIdManager'):
        print("✅ CorrelationIdManager found!")
        manager = logging_module.CorrelationIdManager
        print(f"CorrelationIdManager: {manager}")
    else:
        print("❌ CorrelationIdManager not found")

        print("Step 4: Try manual execution...")
        with open('openhands/server/websocket/logging.py', 'r') as f:
            code = f.read()

        print("File contents preview:")
        lines = code.split('\n')
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:2d}: {line}")

        print("\nExecuting code manually...")
        exec(code, logging_module.__dict__)

        print("After manual execution:")
        contents = [name for name in dir(logging_module) if not name.startswith('_')]
        print(f"Module contents: {contents}")

        if hasattr(logging_module, 'CorrelationIdManager'):
            print("✅ CorrelationIdManager found after manual execution!")
        else:
            print("❌ Still no CorrelationIdManager")

except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
