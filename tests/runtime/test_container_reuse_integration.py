"""Integration tests for container reuse strategies.

These tests verify end-to-end container reuse functionality across multiple runtime sessions,
performance improvements, and edge cases that require real Docker container interactions.
"""

import os
import time

import pytest

from openhands.core.config import OpenHandsConfig, load_openhands_config
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.storage import get_file_store
from openhands.utils.async_utils import call_async_from_sync

from .conftest import _close_test_runtime


@pytest.mark.skipif(
    os.getenv('TEST_RUNTIME', 'docker').lower() != 'docker',
    reason='Integration tests require Docker runtime',
)
class TestContainerReuseIntegration:
    """Integration tests for container reuse functionality."""

    def _create_runtime(
        self,
        temp_dir: str,
        container_reuse_strategy: str = 'none',
        sid: str = None,
    ) -> tuple[DockerRuntime, OpenHandsConfig]:
        """Create a DockerRuntime instance with specified reuse strategy."""
        if sid is None:
            sid = f'test-{int(time.time() * 1000)}'

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
        return runtime, config

    def test_end_to_end_container_reuse_workflow_pause(self, temp_dir):
        """Test complete container reuse workflow with pause strategy."""
        # Create first runtime with pause strategy
        runtime1, config1 = self._create_runtime(temp_dir, 'pause', 'reuse-test-1')

        try:
            # Execute a command to ensure container is ready
            result = call_async_from_sync(
                runtime1.run_in_sandbox, 'echo "first session"'
            )
            assert result.exit_code == 0
            assert 'first session' in result.content

            # Store container details
            original_container_id = runtime1.container.id
            original_container_name = runtime1.container.name

            # Close runtime with pause
            _close_test_runtime(runtime1)

            # Verify container was paused, not removed
            import docker

            client = docker.from_env()
            container = client.containers.get(original_container_id)
            assert container.status == 'paused'

            # Create second runtime with same sid to trigger reuse
            runtime2, config2 = self._create_runtime(temp_dir, 'pause', 'reuse-test-1')

            try:
                # Verify same container was reused
                assert runtime2.container.id == original_container_id
                assert runtime2.container.name == original_container_name
                assert runtime2.container.status == 'running'

                # Verify container is functional after resume
                result = call_async_from_sync(
                    runtime2.run_in_sandbox, 'echo "second session"'
                )
                assert result.exit_code == 0
                assert 'second session' in result.content

                logger.info(f'✅ Successfully reused container {original_container_id}')

            finally:
                _close_test_runtime(runtime2)

        finally:
            # Cleanup: ensure container is removed
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_end_to_end_container_reuse_workflow_keep_alive(self, temp_dir):
        """Test complete container reuse workflow with keep_alive strategy."""
        # Create first runtime with keep_alive strategy
        runtime1, config1 = self._create_runtime(
            temp_dir, 'keep_alive', 'keepalive-test-1'
        )

        try:
            # Create a test file to verify workspace cleanup
            result = call_async_from_sync(
                runtime1.run_in_sandbox,
                'echo "test content" > /workspace/test_file.txt',
            )
            assert result.exit_code == 0

            # Verify file exists
            result = call_async_from_sync(
                runtime1.run_in_sandbox, 'cat /workspace/test_file.txt'
            )
            assert result.exit_code == 0
            assert 'test content' in result.content

            original_container_id = runtime1.container.id
            original_container_name = runtime1.container.name

            # Close runtime (should keep container alive)
            _close_test_runtime(runtime1)

            # Verify container is still running
            import docker

            client = docker.from_env()
            container = client.containers.get(original_container_id)
            assert container.status == 'running'

            # Create second runtime to trigger reuse
            runtime2, config2 = self._create_runtime(
                temp_dir, 'keep_alive', 'keepalive-test-1'
            )

            try:
                # Verify same container was reused
                assert runtime2.container.id == original_container_id
                assert runtime2.container.name == original_container_name

                # Verify workspace was cleaned (test file should be gone)
                result = call_async_from_sync(runtime2.run_in_sandbox, 'ls /workspace/')
                assert result.exit_code == 0
                assert 'test_file.txt' not in result.content

                # Verify container is still functional
                result = call_async_from_sync(
                    runtime2.run_in_sandbox, 'echo "reused session"'
                )
                assert result.exit_code == 0
                assert 'reused session' in result.content

                logger.info(
                    f'✅ Successfully reused keep-alive container {original_container_id}'
                )

            finally:
                _close_test_runtime(runtime2)

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_container_reuse_with_incompatible_images(self, temp_dir):
        """Test that containers with different images are not reused."""
        # Create runtime with default image
        runtime1, config1 = self._create_runtime(temp_dir, 'pause', 'image-test-1')

        try:
            original_container_id = runtime1.container.id
            _close_test_runtime(runtime1)

            # Create runtime with different base image
            runtime2, config2 = self._create_runtime(temp_dir, 'pause', 'image-test-1')
            runtime2.config.sandbox.base_container_image = 'ubuntu:22.04'

            # Force reconnect to test reuse logic
            call_async_from_sync(runtime2.connect)

            try:
                # Should create new container due to image incompatibility
                assert runtime2.container.id != original_container_id
                logger.info('✅ Correctly created new container for incompatible image')

            finally:
                _close_test_runtime(runtime2)

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_performance_improvements_pause_strategy(self, temp_dir):
        """Test that pause strategy provides performance improvements."""
        times = {'first_startup': 0, 'reuse_startup': 0}

        # Measure first startup time
        start_time = time.time()
        runtime1, config1 = self._create_runtime(temp_dir, 'pause', 'perf-test-1')

        try:
            # Wait for full initialization
            result = call_async_from_sync(runtime1.run_in_sandbox, 'echo "ready"')
            assert result.exit_code == 0
            times['first_startup'] = time.time() - start_time

            _close_test_runtime(runtime1)

            # Measure reuse startup time
            start_time = time.time()
            runtime2, config2 = self._create_runtime(temp_dir, 'pause', 'perf-test-1')

            try:
                result = call_async_from_sync(runtime2.run_in_sandbox, 'echo "ready"')
                assert result.exit_code == 0
                times['reuse_startup'] = time.time() - start_time

                # Performance improvement assertion (should be at least 30% faster)
                improvement_ratio = times['first_startup'] / times['reuse_startup']
                logger.info(
                    f'Performance: First={times["first_startup"]:.2f}s, '
                    f'Reuse={times["reuse_startup"]:.2f}s, '
                    f'Improvement={improvement_ratio:.2f}x'
                )

                # Allow some variance in CI environments
                assert improvement_ratio >= 1.3, (
                    f'Expected at least 1.3x improvement, got {improvement_ratio:.2f}x'
                )

            finally:
                _close_test_runtime(runtime2)

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_performance_improvements_keep_alive_strategy(self, temp_dir):
        """Test that keep_alive strategy provides significant performance improvements."""
        times = {'first_startup': 0, 'reuse_startup': 0}

        # Measure first startup time
        start_time = time.time()
        runtime1, config1 = self._create_runtime(
            temp_dir, 'keep_alive', 'keepalive-perf-1'
        )

        try:
            result = call_async_from_sync(runtime1.run_in_sandbox, 'echo "ready"')
            assert result.exit_code == 0
            times['first_startup'] = time.time() - start_time

            _close_test_runtime(runtime1)

            # Measure reuse startup time
            start_time = time.time()
            runtime2, config2 = self._create_runtime(
                temp_dir, 'keep_alive', 'keepalive-perf-1'
            )

            try:
                result = call_async_from_sync(runtime2.run_in_sandbox, 'echo "ready"')
                assert result.exit_code == 0
                times['reuse_startup'] = time.time() - start_time

                # Keep alive should show more significant improvement (at least 2x)
                improvement_ratio = times['first_startup'] / times['reuse_startup']
                logger.info(
                    f'Keep-alive Performance: First={times["first_startup"]:.2f}s, '
                    f'Reuse={times["reuse_startup"]:.2f}s, '
                    f'Improvement={improvement_ratio:.2f}x'
                )

                assert improvement_ratio >= 2.0, (
                    f'Expected at least 2.0x improvement for keep_alive, got {improvement_ratio:.2f}x'
                )

            finally:
                _close_test_runtime(runtime2)

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass

    def test_concurrent_container_reuse_conflict_resolution(self, temp_dir):
        """Test behavior when multiple runtimes try to reuse the same container."""
        # Create and close first runtime
        runtime1, config1 = self._create_runtime(temp_dir, 'pause', 'concurrent-test-1')

        try:
            original_container_id = runtime1.container.id
            _close_test_runtime(runtime1)

            # Create two runtimes simultaneously trying to reuse same container
            runtime2, config2 = self._create_runtime(
                temp_dir, 'pause', 'concurrent-test-1'
            )
            runtime3, config3 = self._create_runtime(
                temp_dir, 'pause', 'concurrent-test-1'
            )

            try:
                # One should reuse, one should create new
                container_ids = {runtime2.container.id, runtime3.container.id}

                # Should have two different containers
                assert len(container_ids) == 2

                # One should be the original, one should be new
                assert original_container_id in container_ids

                # Both should be functional
                result2 = call_async_from_sync(
                    runtime2.run_in_sandbox, 'echo "runtime2"'
                )
                result3 = call_async_from_sync(
                    runtime3.run_in_sandbox, 'echo "runtime3"'
                )

                assert result2.exit_code == 0
                assert result3.exit_code == 0
                assert 'runtime2' in result2.content
                assert 'runtime3' in result3.content

                logger.info('✅ Concurrent reuse conflict resolved correctly')

            finally:
                _close_test_runtime(runtime2)
                _close_test_runtime(runtime3)

        finally:
            try:
                _close_test_runtime(runtime1)
            except Exception:
                pass
