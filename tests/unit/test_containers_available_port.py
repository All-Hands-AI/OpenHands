import unittest
from unittest.mock import Mock, patch
from typing import Set
import docker
from openhands.runtime.impl.docker.containers import next_available_port, get_used_ports

class TestContainerFunctions(unittest.TestCase):
    def test_next_available_port_basic(self):
        exclude: Set[int] = {3000, 3001, 3003}
        port = next_available_port(3000, 3005, exclude)
        self.assertEqual(port, 3002)

    def test_next_available_port_no_exclude(self):
        port = next_available_port(3000, 3005, set())
        self.assertEqual(port, 3000)

    def test_next_available_port_all_excluded(self):
        exclude = {3000, 3001, 3002}
        with self.assertRaises(ValueError):
            next_available_port(3000, 3002, exclude)

    def test_next_available_port_invalid_range(self):
        with self.assertRaises(ValueError):
            next_available_port(3005, 3000, set())  # start > end

    def test_next_available_port_single_port_range(self):
        port = next_available_port(3000, 3000, set())
        self.assertEqual(port, 3000)

    def test_next_available_port_single_port_excluded(self):
        with self.assertRaises(ValueError):
            next_available_port(3000, 3000, {3000})

    @patch('docker.DockerClient')
    def test_get_used_ports_empty(self, mock_docker):
        mock_client = Mock()
        mock_client.containers.list.return_value = []
        mock_docker.return_value = mock_client
        
        used_ports = get_used_ports(mock_client, 3000, 3005, use_host_network=False)
        self.assertEqual(used_ports, set())

    @patch('docker.DockerClient')
    def test_get_used_ports_with_command_ports(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "/openhands/micromamba/bin/micromamba run -n openhands poetry run python -u -m openhands.runtime.action_execution_server 30000 --working-dir /workspace/3cc32b890549423eb8a313305b142da2 --plugins agent_skills jupyter --username openhands --user-id 501",
            "Ports": []
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        used_ports = get_used_ports(mock_client, 30000, 30005, use_host_network=True)
        self.assertEqual(used_ports, {30000})

    @patch('docker.DockerClient')
    def test_get_used_ports_with_public_ports(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "",
            "Ports": [{"PublicPort": 30001}, {"PublicPort": 30002}]
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        used_ports = get_used_ports(mock_client, 30000, 30005, use_host_network=False)
        self.assertEqual(used_ports, {30001, 30002})

    @patch('docker.DockerClient')
    def test_get_used_ports_combined(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "/openhands/micromamba/bin/micromamba run -n openhands poetry run python -u -m openhands.runtime.action_execution_server 30000 --working-dir /workspace/test --plugins agent_skills jupyter --username openhands --user-id 501",
            "Ports": [{"PublicPort": 30001}]
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        # Test both modes
        used_ports_cmd = get_used_ports(mock_client, 30000, 30005, use_host_network=True)
        self.assertEqual(used_ports_cmd, {30000, 30001})
        used_ports_pub = get_used_ports(mock_client, 30000, 30005, use_host_network=False)
        self.assertEqual(used_ports_pub, {30001})

    @patch('docker.DockerClient')
    def test_get_used_ports_out_of_range(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "/openhands/micromamba/bin/micromamba run -n openhands poetry run python -u -m openhands.runtime.action_execution_server 29999 --working-dir /workspace/test",
            "Ports": [{"PublicPort": 30006}]
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        used_ports_cmd = get_used_ports(mock_client, 30000, 30005, use_host_network=True)
        self.assertEqual(used_ports_cmd, set())  # Command port out of range
        used_ports_pub = get_used_ports(mock_client, 30000, 30005, use_host_network=False)
        self.assertEqual(used_ports_pub, set())  # Public port out of range

    @patch('docker.DockerClient')
    def test_get_used_ports_malformed_command(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "malformed command without port",
            "Ports": []
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        used_ports = get_used_ports(mock_client, 30000, 30005, use_host_network=True)
        self.assertEqual(used_ports, set())

    @patch('docker.DockerClient')
    def test_get_used_ports_missing_attrs(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": None,
            "Ports": None
        }  # Missing both Command and Ports
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        used_ports_cmd = get_used_ports(mock_client, 30000, 30005, use_host_network=True)
        self.assertEqual(used_ports_cmd, set())
        used_ports_pub = get_used_ports(mock_client, 30000, 30005, use_host_network=False)
        self.assertEqual(used_ports_pub, set())

    @patch('docker.DockerClient')
    def test_get_used_ports_malformed_port_data(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "",
            "Ports": [{"WrongKey": 30001}, {}]  # Malformed port data
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        used_ports = get_used_ports(mock_client, 30000, 30005, use_host_network=False)
        self.assertEqual(used_ports, set())

    @patch('docker.DockerClient')
    def test_get_used_ports_use_host_network_true(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "/openhands/micromamba/bin/micromamba run -n openhands poetry run python -u -m openhands.runtime.action_execution_server 30010 --working-dir /workspace/test",
            "Ports": [{"PublicPort": 30011}]
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client

        # Should include both the port from the command (30010) and the public port (30011)
        used_ports = get_used_ports(mock_client, 30000, 30020, use_host_network=True)
        self.assertEqual(used_ports, {30010, 30011})

    @patch('docker.DockerClient')
    def test_get_used_ports_use_host_network_false(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.attrs = {
            "Command": "/openhands/micromamba/bin/micromamba run -n openhands poetry run python -u -m openhands.runtime.action_execution_server 30010 --working-dir /workspace/test",
            "Ports": [{"PublicPort": 30011}]
        }
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client

        # Should only include the public port (30011), not the command port
        used_ports = get_used_ports(mock_client, 30000, 30020, use_host_network=False)
        self.assertEqual(used_ports, {30011})

if __name__ == '__main__':
    unittest.main() 