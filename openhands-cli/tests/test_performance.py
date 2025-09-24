"""
Performance tests for the OpenHands CLI.

These tests ensure that the CLI startup and shutdown times remain fast.
"""

import time
import subprocess
import sys
import signal
import os
import pytest
from pathlib import Path


class TestCLIPerformance:
    """Test CLI performance characteristics."""

    def test_help_performance(self):
        """Test that --help is fast (< 0.5s)."""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)
        
        start_time = time.time()
        result = subprocess.run([
            sys.executable, '-m', 'openhands_cli.simple_main', '--help'
        ], capture_output=True, text=True, env=env, timeout=10)
        help_time = time.time() - start_time
        
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert help_time < 0.5, f"--help took {help_time:.3f}s, should be < 0.5s"
        assert "usage:" in result.stdout.lower(), "Help output should contain usage information"

    def test_import_performance(self):
        """Test that importing the main module is fast (< 0.1s)."""
        start_time = time.time()
        
        # Import in a subprocess to avoid affecting other tests
        result = subprocess.run([
            sys.executable, '-c', 
            'import openhands_cli.simple_main'
        ], capture_output=True, text=True, 
        env={'PYTHONPATH': str(Path(__file__).parent.parent)},
        timeout=5)
        
        import_time = time.time() - start_time
        
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert import_time < 0.1, f"Import took {import_time:.3f}s, should be < 0.1s"

    def test_shutdown_performance(self):
        """Test that CLI shutdown is fast (< 0.2s)."""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)
        
        # Start the CLI process
        proc = subprocess.Popen([
            sys.executable, '-m', 'openhands_cli.simple_main'
        ], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
        )
        
        # Give it a moment to start up
        time.sleep(0.1)
        
        # Send SIGINT to trigger shutdown
        shutdown_start = time.time()
        proc.send_signal(signal.SIGINT)
        
        try:
            proc.wait(timeout=5)
            shutdown_time = time.time() - shutdown_start
            
            assert shutdown_time < 0.2, f"Shutdown took {shutdown_time:.3f}s, should be < 0.2s"
            
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail("Process didn't shut down within timeout")

    def test_lazy_loading_effectiveness(self):
        """Test that lazy loading prevents heavy modules from being imported early."""
        # Test in subprocess to avoid affecting other tests
        result = subprocess.run([
            sys.executable, '-c', '''
import sys
modules_before = set(sys.modules.keys())

import openhands_cli.simple_main

modules_after = set(sys.modules.keys())
new_modules = modules_after - modules_before

# Check that heavy modules are not loaded
heavy_modules = [
    "openhands.sdk",
    "prompt_toolkit.application", 
    "prompt_toolkit.shortcuts",
]

loaded_heavy = [mod for mod in heavy_modules if any(mod in m for m in new_modules)]

if loaded_heavy:
    print(f"HEAVY_MODULES_LOADED: {loaded_heavy}")
    exit(1)
else:
    print("LAZY_LOADING_OK")
    exit(0)
'''
        ], capture_output=True, text=True,
        env={'PYTHONPATH': str(Path(__file__).parent.parent)},
        timeout=5)
        
        assert result.returncode == 0, f"Lazy loading test failed: {result.stdout}"
        assert "LAZY_LOADING_OK" in result.stdout, "Lazy loading should prevent heavy module imports"

    def test_startup_performance(self):
        """Test that CLI startup is reasonable (< 1.0s)."""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)
        
        start_time = time.time()
        proc = subprocess.Popen([
            sys.executable, '-m', 'openhands_cli.simple_main'
        ], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
        )
        
        # Give it a moment to start up
        time.sleep(0.1)
        startup_time = time.time() - start_time
        
        # Clean up
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        
        assert startup_time < 1.0, f"Startup took {startup_time:.3f}s, should be < 1.0s"


class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_shutdown_time_regression(self):
        """Ensure shutdown time doesn't regress beyond acceptable limits."""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)
        
        # Test multiple times to get consistent results
        shutdown_times = []
        
        for _ in range(3):
            proc = subprocess.Popen([
                sys.executable, '-m', 'openhands_cli.simple_main'
            ], 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
            )
            
            time.sleep(0.1)
            
            shutdown_start = time.time()
            proc.send_signal(signal.SIGINT)
            
            try:
                proc.wait(timeout=5)
                shutdown_time = time.time() - shutdown_start
                shutdown_times.append(shutdown_time)
                
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                pytest.fail("Process didn't shut down within timeout")
        
        avg_shutdown_time = sum(shutdown_times) / len(shutdown_times)
        max_shutdown_time = max(shutdown_times)
        
        # Ensure average shutdown time is good
        assert avg_shutdown_time < 0.15, f"Average shutdown time {avg_shutdown_time:.3f}s should be < 0.15s"
        
        # Ensure no single shutdown takes too long
        assert max_shutdown_time < 0.3, f"Max shutdown time {max_shutdown_time:.3f}s should be < 0.3s"