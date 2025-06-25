import unittest
from unittest.mock import MagicMock, patch

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.runtime.impl.docker.warm_docker_runtime import WarmDockerRuntime
from openhands.runtime.plugins import PluginRequirement


class TestWarmDockerRuntime(unittest.TestCase):
    """Test the WarmDockerRuntime class."""

    def setUp(self):
        """Set up the test environment."""
        # Clear the warm pool before each test
        WarmDockerRuntime._warm_pool = []

        # Set the warm pool size to a known value
        WarmDockerRuntime.set_warm_pool_size(2)

        # Create mock objects
        self.mock_config = MagicMock(spec=OpenHandsConfig)
        self.mock_event_stream = MagicMock(spec=EventStream)

        # Configure the mock config
        self.mock_config.sandbox = MagicMock()
        self.mock_config.sandbox.local_runtime_url = 'http://localhost'
        self.mock_config.sandbox.base_container_image = 'openhands/base:latest'
        self.mock_config.sandbox.runtime_container_image = 'openhands/runtime:latest'
        self.mock_config.sandbox.keep_runtime_alive = False
        self.mock_config.sandbox.rm_all_containers = False
        self.mock_config.sandbox.runtime_binding_address = '0.0.0.0'
        self.mock_config.sandbox.use_host_network = False
        self.mock_config.sandbox.enable_gpu = False
        self.mock_config.sandbox.runtime_startup_env_vars = {}
        self.mock_config.sandbox.volumes = None
        self.mock_config.workspace_mount_path = None
        self.mock_config.workspace_mount_path_in_sandbox = None
        self.mock_config.workspace_base = '/workspace'
        self.mock_config.debug = False

    def test_warm_pool_size(self):
        """Test setting and getting the warm pool size."""
        # Set the warm pool size
        WarmDockerRuntime.set_warm_pool_size(5)

        # Check that the warm pool size was set correctly
        self.assertEqual(WarmDockerRuntime.get_warm_pool_size(), 5)

    @patch('openhands.runtime.impl.docker.warm_docker_runtime.DockerRuntime.connect')
    @patch(
        'openhands.runtime.impl.docker.warm_docker_runtime.DockerRuntime._init_docker_client'
    )
    def test_plugin_env_key_generation(self, mock_init_docker_client, mock_connect):
        """Test the generation of plugin and environment variable keys."""
        # Create some test plugins and environment variables
        plugins = [
            PluginRequirement(name='plugin1'),
            PluginRequirement(name='plugin2'),
        ]
        env_vars = {
            'VAR1': 'value1',
            'VAR2': 'value2',
        }

        # Generate a key for the plugins and environment variables
        key = WarmDockerRuntime._get_plugin_env_key(plugins, env_vars)

        # Check that the key is as expected
        expected_key = 'plugin1,plugin2|VAR1=value1,VAR2=value2'
        self.assertEqual(key, expected_key)

        # Test with empty plugins and environment variables
        key = WarmDockerRuntime._get_plugin_env_key(None, None)
        self.assertEqual(key, '|')

    @patch('openhands.runtime.impl.docker.warm_docker_runtime.DockerRuntime.connect')
    @patch(
        'openhands.runtime.impl.docker.warm_docker_runtime.DockerRuntime._init_docker_client'
    )
    def test_find_matching_warm_runtime(self, mock_init_docker_client, mock_connect):
        """Test finding a matching warm runtime in the pool."""
        # Create some test plugins and environment variables
        plugins1 = [
            PluginRequirement(name='plugin1'),
            PluginRequirement(name='plugin2'),
        ]
        env_vars1 = {
            'VAR1': 'value1',
            'VAR2': 'value2',
        }

        plugins2 = [
            PluginRequirement(name='plugin3'),
        ]
        env_vars2 = {
            'VAR3': 'value3',
        }

        # Create mock warm runtimes
        mock_runtime1 = MagicMock()
        mock_runtime1.plugins = plugins1
        mock_runtime1.initial_env_vars = env_vars1

        mock_runtime2 = MagicMock()
        mock_runtime2.plugins = plugins2
        mock_runtime2.initial_env_vars = env_vars2

        # Add the mock runtimes to the warm pool
        WarmDockerRuntime._warm_pool = [mock_runtime1, mock_runtime2]

        # Find a matching runtime
        runtime = WarmDockerRuntime._find_matching_warm_runtime(plugins1, env_vars1)

        # Check that the correct runtime was found
        self.assertEqual(runtime, mock_runtime1)

        # Check that the runtime was removed from the pool
        self.assertEqual(len(WarmDockerRuntime._warm_pool), 1)
        self.assertEqual(WarmDockerRuntime._warm_pool[0], mock_runtime2)

        # Try to find a non-existent runtime
        runtime = WarmDockerRuntime._find_matching_warm_runtime(
            [PluginRequirement(name='nonexistent')],
            {'NONEXISTENT': 'value'},
        )

        # Check that no runtime was found
        self.assertIsNone(runtime)

        # Check that the pool was not modified
        self.assertEqual(len(WarmDockerRuntime._warm_pool), 1)
        self.assertEqual(WarmDockerRuntime._warm_pool[0], mock_runtime2)


if __name__ == '__main__':
    unittest.main()
