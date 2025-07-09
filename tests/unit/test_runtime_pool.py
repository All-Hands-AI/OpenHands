"""Tests for the runtime pool functionality."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.runtime.pool import PooledRuntime, RuntimePool
from openhands.storage import get_file_store


class TestRuntimePool:
    """Test cases for RuntimePool class."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any existing singleton
        RuntimePool._instance = None

        # Set up environment variables for testing
        self.original_env = {}
        test_env = {
            'POOLED_RUNTIME_CLASS': 'local',
            'INITIAL_NUM_WARM_SERVERS': '1',
            'TARGET_NUM_WARM_SERVERS': '2',
        }

        for key, value in test_env.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value

    def teardown_method(self):
        """Clean up test environment."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

        # Clean up singleton
        pool = RuntimePool.get_instance()
        if pool.enabled:
            pool.teardown()
        RuntimePool._instance = None

    def test_pool_disabled_when_no_env_var(self):
        """Test that pool is disabled when POOLED_RUNTIME_CLASS is not set."""
        # Clear the environment variable
        os.environ.pop('POOLED_RUNTIME_CLASS', None)

        # Create a new pool instance
        RuntimePool._instance = None
        pool = RuntimePool.get_instance()

        assert not pool.enabled

    def test_pool_enabled_with_valid_runtime_class(self):
        """Test that pool is enabled with valid runtime class."""
        pool = RuntimePool.get_instance()
        assert pool.enabled
        assert pool.runtime_class_name == 'local'
        assert pool.initial_num_warm == 1
        assert pool.target_num_warm == 2

    def test_pool_disabled_with_invalid_runtime_class(self):
        """Test that pool is disabled with invalid runtime class."""
        os.environ['POOLED_RUNTIME_CLASS'] = 'invalid_runtime'

        # Create a new pool instance
        RuntimePool._instance = None
        pool = RuntimePool.get_instance()

        assert not pool.enabled

    @patch('openhands.runtime.pool.RuntimePool._create_runtime')
    def test_pool_setup_and_teardown(self, mock_create_runtime):
        """Test pool setup and teardown."""
        # Mock runtime creation
        mock_runtime = MagicMock()
        mock_create_runtime.return_value = mock_runtime

        pool = RuntimePool.get_instance()

        # Create a minimal config
        config = OpenHandsConfig()

        # Setup the pool
        pool.setup(config)

        # Verify setup was called
        assert pool._config == config
        assert pool.maintenance_thread is not None
        assert pool.maintenance_thread.is_alive()

        # Teardown
        pool.teardown()

        # Verify teardown
        assert not pool.maintenance_thread.is_alive()

    def test_get_runtime_when_pool_disabled(self):
        """Test getting runtime when pool is disabled."""
        # Disable the pool
        os.environ.pop('POOLED_RUNTIME_CLASS', None)
        RuntimePool._instance = None

        pool = RuntimePool.get_instance()

        # Create minimal config and event stream
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir
            file_store = get_file_store(config.file_store, config.file_store_path)
            event_stream = EventStream('test', file_store)

            # Mock the runtime class to avoid actual runtime creation
            with patch('openhands.runtime.pool.get_runtime_cls') as mock_get_cls:
                mock_runtime_cls = MagicMock()
                mock_runtime = MagicMock()
                mock_runtime_cls.return_value = mock_runtime
                mock_get_cls.return_value = mock_runtime_cls

                runtime = pool.get_runtime(config, event_stream)

                # Should create runtime directly, not from pool
                mock_runtime_cls.assert_called_once()
                assert runtime == mock_runtime

    @patch('openhands.runtime.pool.RuntimePool._create_runtime')
    def test_get_runtime_from_pool(self, mock_create_runtime):
        """Test getting runtime from pool."""
        # Mock runtime creation
        mock_runtime = MagicMock()
        mock_create_runtime.return_value = mock_runtime

        pool = RuntimePool.get_instance()

        # Create minimal config
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir
            file_store = get_file_store(config.file_store, config.file_store_path)
            event_stream = EventStream('test', file_store)

            # Setup pool
            pool.setup(config)

            # Add a runtime to the pool manually
            pool.pool.put(mock_runtime)

            # Get runtime from pool
            runtime = pool.get_runtime(config, event_stream)

            assert runtime == mock_runtime
            assert runtime in pool.active_runtimes

            # Pool should be empty now
            assert pool.pool.qsize() == 0

            # Clean up
            pool.teardown()

    @patch('openhands.runtime.pool.RuntimePool._create_runtime')
    def test_return_runtime_to_pool(self, mock_create_runtime):
        """Test returning runtime to pool."""
        # Mock runtime creation and reset
        mock_runtime = MagicMock()
        mock_create_runtime.return_value = mock_runtime

        pool = RuntimePool.get_instance()

        # Create minimal config
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir

            # Setup pool
            pool.setup(config)

            # Add runtime to active set
            pool.active_runtimes.add(mock_runtime)

            # Mock successful reset
            with patch.object(pool, '_reset_runtime', return_value=True):
                pool.return_runtime(mock_runtime)

            # Runtime should be back in pool
            assert pool.pool.qsize() == 1
            assert mock_runtime not in pool.active_runtimes

            # Clean up
            pool.teardown()


class TestPooledRuntime:
    """Test cases for PooledRuntime class."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any existing singleton
        RuntimePool._instance = None

        # Set up environment variables for testing
        self.original_env = {}
        test_env = {
            'POOLED_RUNTIME_CLASS': 'local',
            'INITIAL_NUM_WARM_SERVERS': '1',
            'TARGET_NUM_WARM_SERVERS': '1',
        }

        for key, value in test_env.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value

    def teardown_method(self):
        """Clean up test environment."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

        # Clean up singleton
        pool = RuntimePool.get_instance()
        if pool.enabled:
            pool.teardown()
        RuntimePool._instance = None

    def test_pooled_runtime_initialization(self):
        """Test PooledRuntime initialization."""
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir
            file_store = get_file_store(config.file_store, config.file_store_path)
            event_stream = EventStream('test', file_store)

            runtime = PooledRuntime(config, event_stream)

            assert runtime._actual_runtime is None
            assert runtime._init_config == config
            assert runtime._init_event_stream == event_stream

    @patch('openhands.runtime.pool.RuntimePool.get_runtime')
    def test_pooled_runtime_connect(self, mock_get_runtime):
        """Test PooledRuntime connect method."""
        # Mock the actual runtime
        mock_actual_runtime = MagicMock()
        mock_actual_runtime._runtime_initialized = True
        mock_actual_runtime.runtime_status = 'ready'
        mock_get_runtime.return_value = mock_actual_runtime

        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir
            file_store = get_file_store(config.file_store, config.file_store_path)
            event_stream = EventStream('test', file_store)

            runtime = PooledRuntime(config, event_stream)

            # Test connect
            import asyncio

            asyncio.run(runtime.connect())

            assert runtime._actual_runtime == mock_actual_runtime
            assert runtime._runtime_initialized is True
            assert runtime.runtime_status == 'ready'

    @patch('openhands.runtime.pool.RuntimePool.return_runtime')
    def test_pooled_runtime_close(self, mock_return_runtime):
        """Test PooledRuntime close method."""
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir
            file_store = get_file_store(config.file_store, config.file_store_path)
            event_stream = EventStream('test', file_store)

            runtime = PooledRuntime(config, event_stream)

            # Set up actual runtime
            mock_actual_runtime = MagicMock()
            runtime._actual_runtime = mock_actual_runtime

            # Test close
            runtime.close()

            mock_return_runtime.assert_called_once_with(mock_actual_runtime)
            assert runtime._actual_runtime is None
            assert runtime._runtime_initialized is False

    def test_pooled_runtime_delegation(self):
        """Test that PooledRuntime properly delegates method calls."""
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir
            file_store = get_file_store(config.file_store, config.file_store_path)
            event_stream = EventStream('test', file_store)

            runtime = PooledRuntime(config, event_stream)

            # Set up actual runtime
            mock_actual_runtime = MagicMock()
            mock_actual_runtime.some_method.return_value = 'test_result'
            runtime._actual_runtime = mock_actual_runtime

            # Test delegation
            result = runtime.some_method('arg1', kwarg1='value1')

            mock_actual_runtime.some_method.assert_called_once_with(
                'arg1', kwarg1='value1'
            )
            assert result == 'test_result'

    def test_pooled_runtime_not_connected_error(self):
        """Test that PooledRuntime raises error when not connected."""
        config = OpenHandsConfig()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.file_store_path = temp_dir
            file_store = get_file_store(config.file_store, config.file_store_path)
            event_stream = EventStream('test', file_store)

            runtime = PooledRuntime(config, event_stream)

            # Should raise error when trying to access methods without connecting
            with pytest.raises(RuntimeError, match='PooledRuntime not connected'):
                runtime.run(MagicMock())
