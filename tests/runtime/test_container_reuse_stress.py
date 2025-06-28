"""Stress tests for container reuse strategies.

These tests verify robustness under high load, edge cases, and error conditions
that could occur in production environments.
"""

import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest

from openhands.core.config import load_openhands_config
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.storage import get_file_store
from openhands.utils.async_utils import call_async_from_sync

from .conftest import _close_test_runtime


@pytest.mark.skipif(
    os.getenv('TEST_RUNTIME', 'docker').lower() != 'docker',
    reason='Stress tests require Docker runtime',
)
class TestContainerReuseStress:
    """Stress tests for container reuse functionality."""

    def _create_runtime(
        self,
        temp_dir: str,
        container_reuse_strategy: str = 'none',
        sid: str = None,
    ) -> tuple[DockerRuntime, str]:
        """Create a DockerRuntime instance with specified reuse strategy."""
        if sid is None:
            sid = f'stress-{int(time.time() * 1000)}-{random.randint(1000, 9999)}'

        config = load_openhands_config()
        config.sandbox.container_reuse_strategy = container_reuse_strategy
        config.sandbox.keep_runtime_alive = False
        config.sandbox.force_rebuild_runtime = False
        config.workspace_base = temp_dir
        config.workspace_mount_path = temp_dir
        config.workspace_mount_path_in_sandbox = '/workspace'

        file_store = get_file_store(
            config.file_store,
            config.file_store_path,
            config.file_store_web_hook_url,
            config.file_store_web_hook_headers,
        )
        event_stream = EventStream(sid, file_store)

        runtime = DockerRuntime(
            config=config,
            event_stream=event_stream,
            sid=sid,
            plugins=[],
        )

        call_async_from_sync(runtime.connect)
        return runtime, sid

    def test_container_discovery_with_many_containers(self, temp_dir):
        """Test container discovery performance with many existing containers."""
        created_runtimes = []

        try:
            # Create multiple paused containers to simulate a busy environment
            logger.info('Creating multiple containers for discovery test...')
            for i in range(10):
                runtime, sid = self._create_runtime(
                    temp_dir, 'pause', f'discovery-test-{i}'
                )
                created_runtimes.append(runtime)

                # Execute a command to ensure container is ready
                result = call_async_from_sync(
                    runtime.run_in_sandbox, f'echo "container {i}"'
                )
                assert result.exit_code == 0

                # Pause the container
                _close_test_runtime(runtime)

            # Now test discovery performance with a new runtime
            start_time = time.time()
            target_runtime, target_sid = self._create_runtime(
                temp_dir, 'pause', 'discovery-target'
            )
            discovery_time = time.time() - start_time

            try:
                # Should still be reasonably fast even with many containers
                assert discovery_time < 30.0, (
                    f'Container discovery took too long: {discovery_time:.2f}s'
                )

                # Verify the target runtime works
                result = call_async_from_sync(
                    target_runtime.run_in_sandbox, 'echo "discovery test"'
                )
                assert result.exit_code == 0
                assert 'discovery test' in result.content

                logger.info(
                    f'✅ Container discovery with 10 existing containers: {discovery_time:.2f}s'
                )

            finally:
                _close_test_runtime(target_runtime)

        finally:
            # Cleanup all created runtimes
            for runtime in created_runtimes:
                try:
                    _close_test_runtime(runtime)
                except Exception:
                    pass

    def test_rapid_container_cycling(self, temp_dir):
        """Test rapid creation and destruction of containers with reuse."""
        runtime_count = 5
        runtimes_created = []

        try:
            # Rapidly create and destroy containers
            for i in range(runtime_count):
                runtime, sid = self._create_runtime(
                    temp_dir, 'pause', f'cycle-test-{i}'
                )
                runtimes_created.append(runtime)

                # Quick verification
                result = call_async_from_sync(
                    runtime.run_in_sandbox, f'echo "cycle {i}"'
                )
                assert result.exit_code == 0
                assert f'cycle {i}' in result.content

                # Close immediately
                _close_test_runtime(runtime)

            logger.info(f'✅ Successfully cycled {runtime_count} containers')

        finally:
            for runtime in runtimes_created:
                try:
                    _close_test_runtime(runtime)
                except Exception:
                    pass

    def test_workspace_cleanup_failure_handling(self, temp_dir):
        """Test keep_alive strategy when workspace cleanup fails."""
        runtime1, sid1 = self._create_runtime(
            temp_dir, 'keep_alive', 'cleanup-fail-test'
        )

        try:
            # Create files that might be difficult to clean
            commands = [
                'mkdir -p /workspace/test_dir',
                'echo "test content" > /workspace/test_dir/file.txt',
                'chmod 444 /workspace/test_dir/file.txt',  # Read-only file
                'chmod 555 /workspace/test_dir',  # Read-only directory
            ]

            for cmd in commands:
                result = call_async_from_sync(runtime1.run_in_sandbox, cmd)
                assert result.exit_code == 0

            container_id = runtime1.container.id
            _close_test_runtime(runtime1)

            # Mock workspace cleanup to fail
            with patch.object(
                DockerRuntime, '_clean_workspace_for_reuse'
            ) as mock_cleanup:
                mock_cleanup.side_effect = Exception('Cleanup failed')

                # Should still create new runtime, but won't reuse container
                runtime2, sid2 = self._create_runtime(
                    temp_dir, 'keep_alive', 'cleanup-fail-test'
                )

                try:
                    # Should have created a new container due to cleanup failure
                    assert runtime2.container.id != container_id

                    # Should still be functional
                    result = call_async_from_sync(
                        runtime2.run_in_sandbox, 'echo "new container"'
                    )
                    assert result.exit_code == 0
                    assert 'new container' in result.content

                    logger.info('✅ Gracefully handled workspace cleanup failure')

                finally:
                    _close_test_runtime(runtime2)

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_docker_daemon_connectivity_issues(self, temp_dir):
        """Test graceful handling when Docker daemon is temporarily unavailable."""
        # Create a runtime first
        runtime1, sid1 = self._create_runtime(temp_dir, 'pause', 'daemon-test')

        try:
            result = call_async_from_sync(
                runtime1.run_in_sandbox, 'echo "before disconnect"'
            )
            assert result.exit_code == 0

            _close_test_runtime(runtime1)

            # Mock Docker client to simulate connection issues
            with patch('docker.from_env') as mock_docker:
                mock_docker.side_effect = Exception('Cannot connect to Docker daemon')

                # Should handle the error gracefully
                with pytest.raises(Exception) as exc_info:
                    runtime2, sid2 = self._create_runtime(
                        temp_dir, 'pause', 'daemon-test'
                    )

                # Verify it's a meaningful error message
                assert 'Docker' in str(exc_info.value) or 'daemon' in str(
                    exc_info.value
                )
                logger.info('✅ Gracefully handled Docker daemon connectivity issues')

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_container_name_conflicts_and_resolution(self, temp_dir):
        """Test handling of container naming conflicts during reuse."""
        runtime1, sid1 = self._create_runtime(temp_dir, 'pause', 'conflict-test')

        try:
            original_name = runtime1.container.name
            _close_test_runtime(runtime1)

            # Simulate external container with conflicting name
            import docker

            client = docker.from_env()

            # Create a conflicting container with a similar name pattern
            conflict_container = client.containers.run(
                'ubuntu:22.04',
                'sleep 60',
                name=f'{original_name}-conflict',
                detach=True,
            )

            try:
                # Create new runtime - should handle naming conflicts
                runtime2, sid2 = self._create_runtime(
                    temp_dir, 'pause', 'conflict-test'
                )

                try:
                    # Should successfully create or reuse a container
                    assert runtime2.container is not None

                    # Verify functionality
                    result = call_async_from_sync(
                        runtime2.run_in_sandbox, 'echo "conflict resolved"'
                    )
                    assert result.exit_code == 0
                    assert 'conflict resolved' in result.content

                    logger.info('✅ Successfully resolved container naming conflicts')

                finally:
                    _close_test_runtime(runtime2)

            finally:
                # Cleanup conflict container
                conflict_container.stop()
                conflict_container.remove()

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_memory_usage_patterns_keep_alive(self, temp_dir):
        """Test that keep_alive strategy doesn't cause memory leaks."""
        memory_usage = []
        runtime_cycles = 3

        for cycle in range(runtime_cycles):
            runtime, sid = self._create_runtime(
                temp_dir, 'keep_alive', f'memory-test-{cycle}'
            )

            try:
                # Simulate some work that could cause memory usage
                commands = [
                    'python3 -c "data = list(range(100000)); print(len(data))"',
                    'echo "$(date): Memory test cycle {cycle}"'.format(cycle=cycle),
                    'ls -la /workspace',
                ]

                for cmd in commands:
                    result = call_async_from_sync(runtime.run_in_sandbox, cmd)
                    assert result.exit_code == 0

                # Get basic memory info from container
                result = call_async_from_sync(
                    runtime.run_in_sandbox, 'cat /proc/meminfo | grep MemAvailable'
                )
                if result.exit_code == 0:
                    # Extract memory value (simplified)
                    memory_line = result.content.strip()
                    if 'MemAvailable' in memory_line:
                        memory_kb = int(memory_line.split()[1])
                        memory_usage.append(memory_kb)

            finally:
                _close_test_runtime(runtime)

        # Basic check: memory usage shouldn't drastically decrease over cycles
        # (indicating potential memory leaks)
        if len(memory_usage) >= 2:
            first_memory = memory_usage[0]
            last_memory = memory_usage[-1]
            memory_decrease = (first_memory - last_memory) / first_memory

            # Allow 20% variation (container environments can be variable)
            assert memory_decrease < 0.2, (
                f'Potential memory leak detected: {memory_decrease:.2%} decrease '
                f'from {first_memory}KB to {last_memory}KB'
            )

            logger.info(f'✅ Memory usage stable across {runtime_cycles} cycles')

    def test_concurrent_reuse_stress(self, temp_dir):
        """Stress test with multiple concurrent runtime creations."""
        concurrent_runtimes = 3
        results = []

        def create_and_test_runtime(runtime_id: int) -> dict:
            """Create a runtime and test its functionality."""
            try:
                runtime, sid = self._create_runtime(
                    temp_dir, 'pause', f'concurrent-stress-{runtime_id}'
                )

                # Test basic functionality
                result = call_async_from_sync(
                    runtime.run_in_sandbox, f'echo "runtime {runtime_id} working"'
                )

                success = (
                    result.exit_code == 0
                    and f'runtime {runtime_id} working' in result.content
                )
                container_id = runtime.container.id

                _close_test_runtime(runtime)

                return {
                    'runtime_id': runtime_id,
                    'success': success,
                    'container_id': container_id,
                    'error': None,
                }

            except Exception as e:
                return {
                    'runtime_id': runtime_id,
                    'success': False,
                    'container_id': None,
                    'error': str(e),
                }

        # Execute concurrent runtime creations
        with ThreadPoolExecutor(max_workers=concurrent_runtimes) as executor:
            futures = [
                executor.submit(create_and_test_runtime, i)
                for i in range(concurrent_runtimes)
            ]

            for future in as_completed(futures):
                results.append(future.result())

        # Analyze results
        successful_runtimes = [r for r in results if r['success']]
        failed_runtimes = [r for r in results if not r['success']]

        logger.info(
            f'Concurrent stress test: {len(successful_runtimes)}/{concurrent_runtimes} successful'
        )

        # At least majority should succeed
        assert len(successful_runtimes) >= concurrent_runtimes * 0.8, (
            f'Too many failures in concurrent test: {len(failed_runtimes)} failed'
        )

        # All container IDs should be unique (no accidental reuse)
        container_ids = [
            r['container_id'] for r in successful_runtimes if r['container_id']
        ]
        assert len(container_ids) == len(set(container_ids)), (
            'Duplicate container IDs detected'
        )

        logger.info('✅ Concurrent stress test passed')

    def test_edge_case_container_states(self, temp_dir):
        """Test behavior with containers in various edge case states."""
        runtime1, sid1 = self._create_runtime(temp_dir, 'pause', 'edge-case-test')

        try:
            container_id = runtime1.container.id
            _close_test_runtime(runtime1)

            # Manually manipulate container state to test edge cases
            import docker

            client = docker.from_env()
            container = client.containers.get(container_id)

            # Test with already stopped container
            container.stop()
            assert container.status in ['stopped', 'exited']

            # Try to reuse stopped container
            runtime2, sid2 = self._create_runtime(temp_dir, 'pause', 'edge-case-test')

            try:
                # Should either reuse and restart, or create new container
                assert runtime2.container is not None

                result = call_async_from_sync(
                    runtime2.run_in_sandbox, 'echo "edge case handled"'
                )
                assert result.exit_code == 0
                assert 'edge case handled' in result.content

                logger.info('✅ Successfully handled edge case container states')

            finally:
                _close_test_runtime(runtime2)

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass
