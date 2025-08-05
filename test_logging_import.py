#!/usr/bin/env python3

print("Starting import test...")

try:
    print("1. Testing basic imports...")
    import uuid
    from contextlib import contextmanager
    from datetime import datetime
    from typing import Any, Dict, Optional, Union
    from contextvars import ContextVar
    print("✅ Basic imports successful")

    print("2. Testing openhands.core.logger import...")
    from openhands.core.logger import openhands_logger
    print("✅ openhands_logger import successful")

    print("3. Testing class definition...")
    class TestCorrelationIdManager:
        @staticmethod
        def test_method():
            return "test"

    print("✅ Class definition successful")

    print("4. Testing full logging module...")
    exec(open('openhands/server/websocket/logging.py').read())
    print("✅ Full module execution successful")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
