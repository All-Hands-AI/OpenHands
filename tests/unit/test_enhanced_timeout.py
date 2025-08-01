"""Tests for enhanced timeout handling system."""

import asyncio
import time
from unittest.mock import Mock

import pytest

from openhands.core.config.timeout_config import (
    TimeoutConfig,
    TimeoutContext,
    TimeoutType,
)
from openhands.events.action.browse import BrowseURLAction
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.action.files import FileReadAction, FileWriteAction
from openhands.utils.timeout_manager import TimeoutManager


class TestTimeoutConfig:
    """Test timeout configuration functionality."""

    def test_default_timeout_values(self):
        """Test that default timeout values are reasonable."""
        config = TimeoutConfig()

        # Check that all timeout types have default values
        assert TimeoutType.COMMAND_DEFAULT in config.default_timeouts
        assert TimeoutType.COMMAND_LONG_RUNNING in config.default_timeouts
        assert TimeoutType.RUNTIME_INIT in config.default_timeouts

        # Check that long-running commands have longer timeouts
        assert (
            config.default_timeouts[TimeoutType.COMMAND_LONG_RUNNING]
            > config.default_timeouts[TimeoutType.COMMAND_DEFAULT]
        )

        # Check that max timeouts are higher than defaults
        assert (
            config.max_timeouts[TimeoutType.COMMAND_DEFAULT]
            > config.default_timeouts[TimeoutType.COMMAND_DEFAULT]
        )

    def test_progressive_timeout(self):
        """Test progressive timeout functionality."""
        config = TimeoutConfig()

        # First attempt should use base timeout
        timeout1 = config.get_timeout(TimeoutType.COMMAND_DEFAULT, attempt=1)
        assert timeout1 == config.default_timeouts[TimeoutType.COMMAND_DEFAULT]

        # Second attempt should be longer
        timeout2 = config.get_timeout(TimeoutType.COMMAND_DEFAULT, attempt=2)
        assert timeout2 > timeout1

        # Third attempt should be even longer
        timeout3 = config.get_timeout(TimeoutType.COMMAND_DEFAULT, attempt=3)
        assert timeout3 > timeout2

    def test_adaptive_timeout(self):
        """Test adaptive timeout based on complexity factor."""
        config = TimeoutConfig()

        # Base timeout
        base_timeout = config.get_timeout(
            TimeoutType.COMMAND_DEFAULT, complexity_factor=1.0
        )

        # Complex operation should have longer timeout
        complex_timeout = config.get_timeout(
            TimeoutType.COMMAND_DEFAULT, complexity_factor=2.0
        )
        assert complex_timeout > base_timeout

        # Simple operation should have shorter timeout
        simple_timeout = config.get_timeout(
            TimeoutType.COMMAND_DEFAULT, complexity_factor=0.5
        )
        assert simple_timeout < base_timeout

    def test_max_timeout_enforcement(self):
        """Test that maximum timeout limits are enforced."""
        config = TimeoutConfig()

        # Even with high complexity and attempt number, should not exceed max
        timeout = config.get_timeout(
            TimeoutType.COMMAND_DEFAULT, attempt=10, complexity_factor=10.0
        )
        assert timeout <= config.max_timeouts[TimeoutType.COMMAND_DEFAULT]

    def test_custom_timeout(self):
        """Test custom timeout override."""
        config = TimeoutConfig()
        custom_value = 300.0

        timeout = config.get_timeout(
            TimeoutType.COMMAND_DEFAULT, custom_timeout=custom_value
        )
        assert timeout == custom_value


class TestTimeoutContext:
    """Test timeout context functionality."""

    def test_timeout_context_creation(self):
        """Test timeout context creation."""
        config = TimeoutConfig()
        context = TimeoutContext(
            config,
            TimeoutType.COMMAND_DEFAULT,
            'test_operation',
            attempt=2,
            complexity_factor=1.5,
        )

        assert context.timeout_type == TimeoutType.COMMAND_DEFAULT
        assert context.operation_name == 'test_operation'
        assert context.attempt == 2
        assert context.complexity_factor == 1.5
        assert context.timeout_value > 0

    def test_timeout_message_generation(self):
        """Test timeout message generation."""
        config = TimeoutConfig()
        context = TimeoutContext(
            config, TimeoutType.COMMAND_DEFAULT, 'test_command', attempt=2
        )

        message = context.get_timeout_message(150.0)
        assert 'test_command' in message
        assert '150.0 seconds' in message
        assert 'attempt 2' in message
        assert 'Suggestions:' in message

    def test_recovery_suggestions(self):
        """Test that recovery suggestions are context-appropriate."""
        config = TimeoutConfig()

        # Command timeout should have command-specific suggestions
        context = TimeoutContext(config, TimeoutType.COMMAND_DEFAULT, 'bash_command')
        message = context.get_timeout_message(60.0)
        assert 'Send an empty command' in message
        assert "Send 'C-c'" in message

        # Runtime init timeout should have runtime-specific suggestions
        context = TimeoutContext(config, TimeoutType.RUNTIME_INIT, 'runtime_startup')
        message = context.get_timeout_message(300.0)
        assert 'runtime logs' in message
        assert 'dependencies' in message


class TestTimeoutManager:
    """Test timeout manager functionality."""

    def test_timeout_manager_creation(self):
        """Test timeout manager creation."""
        config = TimeoutConfig()
        manager = TimeoutManager(config)

        assert manager.timeout_config == config
        assert len(manager._active_operations) == 0

    def test_timeout_context_creation(self):
        """Test timeout context creation through manager."""
        manager = TimeoutManager()
        context = manager.get_timeout_context(
            TimeoutType.COMMAND_DEFAULT, 'test_op', attempt=1, complexity_factor=1.0
        )

        assert isinstance(context, TimeoutContext)
        assert context.timeout_type == TimeoutType.COMMAND_DEFAULT
        assert context.operation_name == 'test_op'

    def test_complexity_factor_estimation(self):
        """Test complexity factor estimation."""
        manager = TimeoutManager()

        # Small data should have factor close to 1
        factor = manager.estimate_complexity_factor('test', data_size=1024)
        assert factor == 1.0

        # Large data should have higher factor
        factor = manager.estimate_complexity_factor('test', data_size=50 * 1024 * 1024)
        assert factor > 1.0

        # Network operations should have higher factor
        factor = manager.estimate_complexity_factor('test', network_involved=True)
        assert factor > 1.0

        # CPU intensive operations should have higher factor
        factor = manager.estimate_complexity_factor('test', cpu_intensive=True)
        assert factor > 1.0

    @pytest.mark.asyncio
    async def test_async_timeout_operation(self):
        """Test async timeout operation context manager."""
        manager = TimeoutManager()

        async def quick_operation():
            await asyncio.sleep(0.1)
            return 'success'

        # Should complete successfully
        async with manager.async_timeout_operation(
            TimeoutType.COMMAND_DEFAULT, 'quick_test', custom_timeout=1.0
        ) as context:
            result = await quick_operation()
            assert result == 'success'
            assert context.timeout_value == 1.0

    @pytest.mark.asyncio
    async def test_async_timeout_operation_timeout(self):
        """Test async timeout operation with actual timeout."""
        manager = TimeoutManager()

        async def slow_operation():
            await asyncio.sleep(2.0)
            return 'should_not_reach'

        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            async with manager.async_timeout_operation(
                TimeoutType.COMMAND_DEFAULT, 'slow_test', custom_timeout=0.5
            ):
                await asyncio.wait_for(slow_operation(), timeout=0.5)

    def test_active_operations_tracking(self):
        """Test tracking of active operations."""
        manager = TimeoutManager()

        with manager.timeout_operation(TimeoutType.COMMAND_DEFAULT, 'test_operation'):
            # Should have one active operation
            active_ops = manager.get_active_operations()
            assert len(active_ops) == 1

            # Check operation details
            op_info = list(active_ops.values())[0]
            assert op_info['operation_name'] == 'test_operation'
            assert op_info['timeout_type'] == TimeoutType.COMMAND_DEFAULT.value
            assert op_info['elapsed_time'] >= 0
            assert op_info['remaining_time'] > 0

        # Should be cleaned up after context exit
        active_ops = manager.get_active_operations()
        assert len(active_ops) == 0

    def test_operation_cancellation(self):
        """Test operation cancellation functionality."""
        manager = TimeoutManager()

        # Test cancelling non-existent operation
        assert not manager.cancel_operation('non_existent')

        # Test cancelling active operation
        with manager.timeout_operation(
            TimeoutType.COMMAND_DEFAULT, 'test_cancellation'
        ):
            active_ops = manager.get_active_operations()
            assert len(active_ops) == 1

            operation_id = list(active_ops.keys())[0]

            # Cancel the operation
            assert manager.cancel_operation(operation_id)

            # Should be removed from active operations
            active_ops = manager.get_active_operations()
            assert len(active_ops) == 0

    @pytest.mark.asyncio
    async def test_async_operation_cancellation(self):
        """Test async operation cancellation."""
        manager = TimeoutManager()

        async def long_running_operation():
            await asyncio.sleep(10)  # Long operation
            return 'completed'

        # Start operation and cancel it
        async with manager.async_timeout_operation(
            TimeoutType.COMMAND_DEFAULT, 'async_cancellation_test'
        ):
            active_ops = manager.get_active_operations()
            operation_id = list(active_ops.keys())[0]

            # Start the operation in background
            task = asyncio.create_task(long_running_operation())
            manager._operation_tasks[operation_id] = task

            # Cancel the operation
            assert manager.cancel_operation(operation_id)

            # Task should be cancelled
            with pytest.raises(asyncio.CancelledError):
                await task

    def test_cancel_all_operations(self):
        """Test cancelling all operations."""
        manager = TimeoutManager()

        # Create multiple operations
        contexts = []
        for i in range(3):
            context = manager.get_timeout_context(
                TimeoutType.COMMAND_DEFAULT, f'test_op_{i}'
            )
            contexts.append(context)

            # Simulate active operation
            operation_id = f'test_op_{i}_{id(context)}'
            manager._active_operations[operation_id] = {
                'context': context,
                'start_time': time.time(),
                'operation_name': f'test_op_{i}',
                'timeout_type': TimeoutType.COMMAND_DEFAULT,
            }

        # Should have 3 active operations
        assert len(manager.get_active_operations()) == 3

        # Cancel all operations
        cancelled_count = manager.cancel_all_operations()
        assert cancelled_count == 3

        # Should have no active operations
        assert len(manager.get_active_operations()) == 0


class TestRuntimeTimeoutIntegration:
    """Test integration with runtime timeout handling."""

    def test_command_timeout_type_detection(self):
        """Test that commands get appropriate timeout types."""
        from openhands.runtime.base import Runtime

        # Mock runtime for testing
        runtime = Mock(spec=Runtime)
        runtime._get_timeout_type_for_action = (
            Runtime._get_timeout_type_for_action.__get__(runtime)
        )

        # Network command should get network timeout
        cmd = CmdRunAction(command='git clone https://github.com/example/repo.git')
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.COMMAND_NETWORK

        # Build command should get long-running timeout
        cmd = CmdRunAction(command='make -j4')
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.COMMAND_LONG_RUNNING

        # Interactive command should get interactive timeout
        cmd = CmdRunAction(command='vim file.txt', is_input=True)
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.COMMAND_INTERACTIVE

        # Regular command should get default timeout
        cmd = CmdRunAction(command='ls -la')
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.COMMAND_DEFAULT

    def test_python_code_timeout_type_detection(self):
        """Test that Python code gets appropriate timeout types."""
        from openhands.runtime.base import Runtime

        runtime = Mock(spec=Runtime)
        runtime._get_timeout_type_for_action = (
            Runtime._get_timeout_type_for_action.__get__(runtime)
        )

        # Network code should get network timeout
        cmd = IPythonRunCellAction(
            code="import requests; requests.get('http://example.com')"
        )
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.COMMAND_NETWORK

        # CPU-intensive code should get long-running timeout
        cmd = IPythonRunCellAction(
            code='import numpy as np; np.random.rand(10000, 10000)'
        )
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.COMMAND_LONG_RUNNING

        # Regular code should get default timeout
        cmd = IPythonRunCellAction(code="print('hello world')")
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.COMMAND_DEFAULT

    def test_browser_action_timeout_types(self):
        """Test that browser actions get appropriate timeout types."""
        from openhands.runtime.base import Runtime

        runtime = Mock(spec=Runtime)
        runtime._get_timeout_type_for_action = (
            Runtime._get_timeout_type_for_action.__get__(runtime)
        )

        # URL navigation should get navigation timeout
        cmd = BrowseURLAction(url='https://example.com')
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.BROWSER_NAVIGATION

    def test_file_action_timeout_types(self):
        """Test that file actions get appropriate timeout types."""
        from openhands.runtime.base import Runtime

        runtime = Mock(spec=Runtime)
        runtime._get_timeout_type_for_action = (
            Runtime._get_timeout_type_for_action.__get__(runtime)
        )

        # File read should get read timeout
        cmd = FileReadAction(path='/tmp/test.txt')
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.FILE_READ

        # File write should get write timeout
        cmd = FileWriteAction(path='/tmp/test.txt', content='test')
        timeout_type = runtime._get_timeout_type_for_action(cmd)
        assert timeout_type == TimeoutType.FILE_WRITE


class TestTimeoutSuggestions:
    """Test timeout suggestion functionality."""

    def test_bash_timeout_suggestions(self):
        """Test that bash timeout suggestions are appropriate."""
        from openhands.runtime.utils.bash import BashSession

        session = BashSession('/tmp', 'test')

        # Package installation suggestions
        suggestions = session._get_timeout_suggestions('npm install', 'no_change')
        assert 'package installation' in suggestions.lower()
        assert 'network' in suggestions.lower()

        # Git operation suggestions
        suggestions = session._get_timeout_suggestions('git clone', 'hard_timeout')
        assert 'git operations' in suggestions.lower()
        assert 'repository size' in suggestions.lower()

        # Compilation suggestions
        suggestions = session._get_timeout_suggestions('make -j4', 'no_change')
        assert 'compilation' in suggestions.lower()
        assert 'parallel' in suggestions.lower()

        # Docker suggestions
        suggestions = session._get_timeout_suggestions('docker build', 'hard_timeout')
        assert 'docker' in suggestions.lower()
        assert 'image size' in suggestions.lower()

    def test_general_timeout_suggestions(self):
        """Test general timeout suggestions."""
        from openhands.runtime.utils.bash import BashSession

        session = BashSession('/tmp', 'test')

        # No-change timeout should suggest waiting
        suggestions = session._get_timeout_suggestions('any_command', 'no_change')
        assert 'empty command' in suggestions.lower()
        assert 'c-c' in suggestions.lower()

        # Hard timeout should suggest process termination info
        suggestions = session._get_timeout_suggestions('any_command', 'hard_timeout')
        assert 'forcibly terminated' in suggestions.lower()
        assert 'longer timeout' in suggestions.lower()


if __name__ == '__main__':
    pytest.main([__file__])
