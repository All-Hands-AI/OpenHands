import asyncio
import os
import signal
import subprocess
import time
from unittest.mock import MagicMock

import pytest

from openhands.core.config import AppConfig
from openhands.events import EventStream
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def config():
    return AppConfig()


@pytest.fixture
def event_stream():
    return EventStream("test", file_store=InMemoryFileStore({}))


@pytest.fixture
def local_runtime(config, event_stream):
    runtime = LocalRuntime(config, event_stream)
    yield runtime
    runtime.close()


@pytest.mark.asyncio
async def test_terminate_processes_graceful(local_runtime):
    # Start a process that handles SIGTERM gracefully
    process = subprocess.Popen([
        "python3", "-c",
        "import signal, time; signal.signal(signal.SIGTERM, lambda s,f: exit(0)); time.sleep(10)"
    ])
    
    # Wait for process to start
    await asyncio.sleep(0.1)
    
    start = time.time()
    await local_runtime.terminate_processes()
    duration = time.time() - start
    
    assert process.poll() is not None  # Process terminated
    assert duration < 1  # Should terminate quickly
    assert process.returncode == 0  # Graceful termination


@pytest.mark.asyncio
async def test_terminate_processes_force(local_runtime):
    # Start a process that ignores SIGTERM
    process = subprocess.Popen([
        "python3", "-c",
        "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(10)"
    ])
    
    # Wait for process to start
    await asyncio.sleep(0.1)
    
    start = time.time()
    await local_runtime.terminate_processes()
    duration = time.time() - start
    
    assert process.poll() is not None  # Process terminated
    assert duration < 1  # Should not wait full timeout
    assert process.returncode != 0  # Force killed


@pytest.mark.asyncio
async def test_terminate_processes_nested(local_runtime):
    # Start a parent process that spawns a child process
    parent = subprocess.Popen([
        "python3", "-c",
        """
import subprocess, signal, time
child = subprocess.Popen(['python3', '-c', 'import time; time.sleep(20)'])
signal.signal(signal.SIGTERM, lambda s,f: exit(0))
time.sleep(10)
        """
    ])
    
    # Wait for processes to start
    await asyncio.sleep(0.1)
    
    # Get child process
    ps_output = subprocess.check_output(['ps', '--ppid', str(parent.pid), '-o', 'pid', '--no-headers']).decode()
    child_pid = int(ps_output.strip())
    
    await local_runtime.terminate_processes()
    
    assert parent.poll() is not None  # Parent terminated
    assert not os.path.exists(f'/proc/{child_pid}')  # Child terminated


@pytest.mark.asyncio
async def test_terminate_processes_concurrent(local_runtime):
    # Start multiple processes
    processes = [
        subprocess.Popen(["python3", "-c", "import time; time.sleep(10)"])
        for _ in range(5)
    ]
    
    # Wait for processes to start
    await asyncio.sleep(0.1)
    
    await local_runtime.terminate_processes()
    
    # All processes should be terminated
    for p in processes:
        assert p.poll() is not None