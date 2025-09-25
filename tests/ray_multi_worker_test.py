"""Comprehensive tests for Ray multi-worker functionality."""

import asyncio
import time
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch

import ray

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.llm.llm_registry import LLMRegistry
from openhands.storage import get_file_store
from openhands.runtime.impl.ray.worker_pool import RayWorkerPool, WorkerSelectionStrategy, WorkerMetrics
from openhands.runtime.impl.ray.session_manager import SessionManager, SessionType
from openhands.runtime.impl.ray.ray_runtime import RayRuntime


class TestRayWorkerPool:
    """Test suite for RayWorkerPool functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_ray(self):
        """Setup and teardown Ray for each test."""
        if not ray.is_initialized():
            ray.init(local_mode=True, ignore_reinit_error=True)
        yield
        # Cleanup is handled by Ray's shutdown
    
    @pytest.fixture
    def worker_pool(self):
        """Create a test worker pool."""
        return RayWorkerPool(
            pool_size=2,
            max_pool_size=4,
            selection_strategy=WorkerSelectionStrategy.LEAST_BUSY
        )
    
    @pytest.mark.asyncio
    async def test_worker_pool_initialization(self, worker_pool):
        """Test worker pool initialization creates correct number of workers."""
        await worker_pool.initialize()
        
        assert len(worker_pool.workers) == 2
        assert len(worker_pool.metrics) == 2
        assert worker_pool._initialized
        
        # Test pool statistics
        stats = worker_pool.get_pool_stats()
        assert stats['pool_size'] == 2
        assert stats['healthy_workers'] >= 0
        
        await worker_pool.shutdown()
    
    @pytest.mark.asyncio
    async def test_worker_selection_strategies(self, worker_pool):
        """Test different worker selection strategies."""
        await worker_pool.initialize()
        
        # Test least busy strategy (default)
        worker_id_1, worker_ref_1 = await worker_pool.get_worker()
        worker_id_2, worker_ref_2 = await worker_pool.get_worker()
        
        assert worker_id_1 in worker_pool.workers
        assert worker_id_2 in worker_pool.workers
        assert worker_ref_1 is not None
        assert worker_ref_2 is not None
        
        # Test session affinity
        session_id = "test_session_123"
        worker_id_3, worker_ref_3 = await worker_pool.get_worker(session_id)
        worker_id_4, worker_ref_4 = await worker_pool.get_worker(session_id)
        
        # Should return same worker for same session
        assert worker_id_3 == worker_id_4
        assert worker_ref_3 == worker_ref_4
        
        await worker_pool.shutdown()
    
    @pytest.mark.asyncio
    async def test_action_execution(self, worker_pool):
        """Test action execution through worker pool."""
        await worker_pool.initialize()
        
        # Test command execution
        action_data = {
            'type': 'CmdRunAction',
            'command': 'echo "Hello Multi-Worker"',
            'timeout': 30
        }
        
        result = await worker_pool.execute_action(action_data)
        
        assert result.get('exit_code') == 0
        assert 'Hello Multi-Worker' in result.get('stdout', '')
        
        # Test metrics were recorded
        stats = worker_pool.get_pool_stats()
        assert stats['total_requests'] > 0
        
        await worker_pool.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_actions(self, worker_pool):
        """Test concurrent action execution across multiple workers."""
        await worker_pool.initialize()
        
        # Create multiple concurrent actions
        actions = [
            {
                'type': 'CmdRunAction',
                'command': f'echo "Worker task {i}"',
                'timeout': 30
            }
            for i in range(5)
        ]
        
        # Execute actions concurrently
        tasks = [
            worker_pool.execute_action(action_data, f"session_{i}")
            for i, action_data in enumerate(actions)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All actions should succeed
        for i, result in enumerate(results):
            assert result.get('exit_code') == 0
            assert f'Worker task {i}' in result.get('stdout', '')
        
        # Check that work was distributed
        stats = worker_pool.get_pool_stats()
        assert stats['total_requests'] == 5
        
        await worker_pool.shutdown()
    
    @pytest.mark.asyncio
    async def test_worker_failure_and_recovery(self, worker_pool):
        """Test worker failure handling and replacement."""
        await worker_pool.initialize()
        
        initial_workers = set(worker_pool.workers.keys())
        
        # Force kill one worker to simulate failure
        worker_to_kill = list(worker_pool.workers.keys())[0]
        ray.kill(worker_pool.workers[worker_to_kill])
        
        # Mark worker as failed
        worker_pool.metrics[worker_to_kill].failed_requests = 100
        worker_pool.metrics[worker_to_kill].total_requests = 100
        worker_pool.metrics[worker_to_kill].update_health()
        
        # Trigger health check
        await worker_pool._perform_health_checks()
        
        # Should have created replacement worker
        assert len(worker_pool.workers) == 2
        final_workers = set(worker_pool.workers.keys())
        
        # At least one worker should be different (replacement)
        assert initial_workers != final_workers
        
        await worker_pool.shutdown()


class TestSessionManager:
    """Test suite for SessionManager functionality."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a test session manager."""
        return SessionManager(default_timeout=60, cleanup_interval=10)
    
    @pytest.mark.asyncio
    async def test_session_creation_and_management(self, session_manager):
        """Test session creation, assignment, and cleanup."""
        await session_manager.initialize()
        
        # Create different types of sessions
        ephemeral_session = session_manager.create_session(
            session_type=SessionType.EPHEMERAL
        )
        ipython_session = session_manager.create_session(
            session_type=SessionType.IPYTHON,
            worker_id="worker_1"
        )
        
        assert ephemeral_session != ipython_session
        assert len(session_manager.sessions) == 2
        
        # Test session retrieval and access tracking
        session_info = session_manager.get_session(ipython_session)
        assert session_info is not None
        assert session_info.session_type == SessionType.IPYTHON
        assert session_info.worker_id == "worker_1"
        assert session_info.access_count > 0
        
        # Test worker assignment
        success = session_manager.assign_worker(ephemeral_session, "worker_2")
        assert success
        
        ephemeral_info = session_manager.get_session(ephemeral_session)
        assert ephemeral_info.worker_id == "worker_2"
        
        # Test session termination
        terminated = session_manager.terminate_session(ephemeral_session)
        assert terminated
        assert len(session_manager.sessions) == 1
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_migration(self, session_manager):
        """Test session migration between workers."""
        await session_manager.initialize()
        
        # Create a stateful session
        session_id = session_manager.create_session(
            session_type=SessionType.IPYTHON,
            worker_id="worker_1"
        )
        
        # Test migration
        migrated = await session_manager.migrate_session(
            session_id, "worker_1", "worker_2"
        )
        assert migrated
        
        # Verify worker assignment changed
        session_info = session_manager.get_session(session_id)
        assert session_info.worker_id == "worker_2"
        
        await session_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_worker_failure_cleanup(self, session_manager):
        """Test cleanup of sessions when worker fails."""
        await session_manager.initialize()
        
        # Create sessions assigned to a worker
        session1 = session_manager.create_session(
            session_type=SessionType.EPHEMERAL,
            worker_id="failed_worker"
        )
        session2 = session_manager.create_session(
            session_type=SessionType.IPYTHON,
            worker_id="failed_worker"
        )
        
        # Simulate worker failure
        session_manager.cleanup_worker_sessions("failed_worker")
        
        # Ephemeral session should be terminated
        # IPython session should be marked for migration
        remaining_sessions = list(session_manager.sessions.keys())
        
        # Should have cleaned up appropriately based on session types
        assert len(remaining_sessions) <= 1  # At most the IPython session remains
        
        await session_manager.shutdown()


class TestRayRuntimeIntegration:
    """Integration tests for the complete Ray runtime system."""
    
    @pytest.fixture(autouse=True)
    def setup_ray(self):
        """Setup Ray for integration tests."""
        if not ray.is_initialized():
            ray.init(local_mode=True, ignore_reinit_error=True)
        yield
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = OpenHandsConfig()
        # Set Ray-specific config
        config.sandbox.ray_worker_pool_size = 2
        config.sandbox.ray_max_pool_size = 4
        config.sandbox.ray_selection_strategy = 'least_busy'
        return config
    
    @pytest.fixture
    def mock_event_stream(self):
        """Create mock event stream."""
        return MagicMock(spec=EventStream)
    
    @pytest.fixture
    def mock_llm_registry(self, config):
        """Create mock LLM registry."""
        return LLMRegistry(config)
    
    def test_ray_runtime_initialization(self, config, mock_event_stream, mock_llm_registry):
        """Test Ray runtime initialization with worker pool."""
        runtime = RayRuntime(
            config=config,
            event_stream=mock_event_stream,
            llm_registry=mock_llm_registry,
            sid="test_session"
        )
        
        assert runtime.worker_pool is not None
        assert runtime.session_manager is not None
        assert runtime.session_id == "test_session"
        
        # Test that workspace is created
        assert os.path.exists(runtime.workspace_path)
        
        # Cleanup
        runtime.close()
    
    @pytest.mark.asyncio
    async def test_ray_runtime_connection(self, config, mock_event_stream, mock_llm_registry):
        """Test Ray runtime connection and basic functionality."""
        runtime = RayRuntime(
            config=config,
            event_stream=mock_event_stream,
            llm_registry=mock_llm_registry,
            sid="test_connection"
        )
        
        # Test connection
        await runtime.connect()
        assert runtime._runtime_initialized
        
        # Test that worker pool is initialized
        assert runtime.worker_pool._initialized
        assert len(runtime.worker_pool.workers) == 2
        
        # Test session is created
        assert "test_connection" in runtime.session_manager.sessions
        
        # Cleanup
        runtime.close()
    
    def test_ray_runtime_action_execution(self, config, mock_event_stream, mock_llm_registry):
        """Test action execution through the distributed runtime."""
        runtime = RayRuntime(
            config=config,
            event_stream=mock_event_stream,
            llm_registry=mock_llm_registry,
            sid="test_actions"
        )
        
        # Mock action objects
        class MockCmdAction:
            def __init__(self, command, timeout=60):
                self.command = command
                self.timeout = timeout
                self.id = "test_cmd_123"
        
        class MockFileWriteAction:
            def __init__(self, path, content):
                self.path = path
                self.content = content
        
        # Initialize runtime
        asyncio.get_event_loop().run_until_complete(runtime.connect())
        
        try:
            # Test command execution
            cmd_action = MockCmdAction("echo 'Multi-worker test'")
            result = runtime.run(cmd_action)
            
            assert hasattr(result, 'content')
            assert hasattr(result, 'exit_code')
            assert result.exit_code == 0
            assert 'Multi-worker test' in result.content
            
            # Test file operations
            test_file = os.path.join(runtime.workspace_path, "test_file.txt")
            write_action = MockFileWriteAction(test_file, "Hello distributed world!")
            write_result = runtime.write(write_action)
            
            assert hasattr(write_result, 'path')
            assert write_result.path == test_file
            
            # Verify file was actually written
            assert os.path.exists(test_file)
            with open(test_file, 'r') as f:
                content = f.read()
                assert content == "Hello distributed world!"
                
        finally:
            # Cleanup
            runtime.close()
    
    def test_ray_runtime_worker_pool_statistics(self, config, mock_event_stream, mock_llm_registry):
        """Test that worker pool statistics are properly tracked."""
        runtime = RayRuntime(
            config=config,
            event_stream=mock_event_stream,
            llm_registry=mock_llm_registry,
            sid="test_stats"
        )
        
        # Initialize runtime
        asyncio.get_event_loop().run_until_complete(runtime.connect())
        
        try:
            # Execute some actions to generate statistics
            class MockCmdAction:
                def __init__(self, command):
                    self.command = command
                    self.timeout = 30
                    self.id = "test_stats_cmd"
            
            for i in range(3):
                action = MockCmdAction(f"echo 'Stats test {i}'")
                result = runtime.run(action)
                assert result.exit_code == 0
            
            # Check worker pool statistics
            stats = runtime.worker_pool.get_pool_stats()
            
            assert stats['pool_size'] == 2
            assert stats['total_requests'] == 3
            assert stats['active_sessions'] >= 1
            assert stats['failure_rate'] == 0.0  # All should succeed
            
            # Check session manager statistics
            session_stats = runtime.session_manager.get_stats()
            assert session_stats['total_sessions'] >= 1
            assert session_stats['active_sessions'] >= 1
            
        finally:
            runtime.close()


@pytest.mark.integration
class TestRayRuntimePerformance:
    """Performance tests for Ray runtime multi-worker system."""
    
    @pytest.fixture(autouse=True)
    def setup_ray(self):
        """Setup Ray for performance tests."""
        if not ray.is_initialized():
            ray.init(local_mode=True, ignore_reinit_error=True)
        yield
    
    @pytest.fixture
    def performance_config(self):
        """Create config optimized for performance testing."""
        config = OpenHandsConfig()
        config.sandbox.ray_worker_pool_size = 4
        config.sandbox.ray_max_pool_size = 8
        config.sandbox.ray_selection_strategy = 'least_busy'
        return config
    
    def test_concurrent_execution_performance(self, performance_config):
        """Test performance of concurrent action execution."""
        runtime = RayRuntime(
            config=performance_config,
            event_stream=MagicMock(),
            llm_registry=LLMRegistry(performance_config),
            sid="perf_test"
        )
        
        asyncio.get_event_loop().run_until_complete(runtime.connect())
        
        try:
            class MockCmdAction:
                def __init__(self, command, action_id):
                    self.command = command
                    self.timeout = 30
                    self.id = action_id
            
            # Measure concurrent execution time
            start_time = time.time()
            
            # Execute multiple actions
            results = []
            for i in range(10):
                action = MockCmdAction(f"echo 'Perf test {i}' && sleep 0.1", f"perf_{i}")
                result = runtime.run(action)
                results.append(result)
            
            execution_time = time.time() - start_time
            
            # All actions should succeed
            for result in results:
                assert result.exit_code == 0
            
            # With 4 workers, concurrent execution should be faster than sequential
            # Expected: ~0.3 seconds (3 batches of 0.1s sleep with 4 workers)
            # vs >1.0 seconds if sequential
            assert execution_time < 0.8, f"Execution took {execution_time}s, expected < 0.8s with parallel execution"
            
            # Verify work distribution
            stats = runtime.worker_pool.get_pool_stats()
            assert stats['total_requests'] == 10
            
        finally:
            runtime.close()
    
    def test_session_affinity_performance(self, performance_config):
        """Test that session affinity maintains performance while preserving state."""
        runtime = RayRuntime(
            config=performance_config,
            event_stream=MagicMock(),
            llm_registry=LLMRegistry(performance_config),
            sid="affinity_test"
        )
        
        asyncio.get_event_loop().run_until_complete(runtime.connect())
        
        try:
            class MockIPythonAction:
                def __init__(self, code, action_id):
                    self.code = code
                    self.id = action_id
            
            # Execute IPython actions that should maintain session affinity
            start_time = time.time()
            
            actions = [
                MockIPythonAction("x = 42", "ipython_1"),
                MockIPythonAction("y = x * 2", "ipython_2"), 
                MockIPythonAction("print(f'Result: {y}')", "ipython_3")
            ]
            
            results = []
            for action in actions:
                result = runtime.run_ipython(action)
                results.append(result)
            
            execution_time = time.time() - start_time
            
            # All actions should execute quickly due to session affinity
            assert execution_time < 5.0, f"IPython session execution took {execution_time}s"
            
            # Check session management
            session_stats = runtime.session_manager.get_stats()
            assert session_stats['total_sessions'] >= 1
            
        finally:
            runtime.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])