from typing import List, Set
import docker
from docker.models.containers import Container
import re

from openhands.core.logger import openhands_logger as logger

def stop_all_containers(prefix: str) -> None:
    docker_client = docker.from_env()
    try:
        containers = docker_client.containers.list(all=True)
        for container in containers:
            try:
                if container.name.startswith(prefix):
                    container.stop()
            except docker.errors.APIError:
                pass
            except docker.errors.NotFound:
                pass
    except docker.errors.NotFound:  # yes, this can happen!
        pass
    finally:
        docker_client.close()

def next_available_port(start: int, end: int, exclude: Set[int]) -> int:
        for port in range(start, end + 1):
            if port not in exclude:
                return port
        raise ValueError("No valid ports available in range")
    
def get_used_ports(docker_client: docker.DockerClient, start: int, end: int) -> Set[int]:
    containers: List[Container] = docker_client.containers.list(all=True, sparse=True)
    used_ports: Set[int] = set()
    for container in containers:
        # Get command string, defaulting to empty string if not present
        # if use_host_network is false, the action_execution_server port is already mapped toPublicPort
        docker_command = container.attrs.get("Command", "")
        if isinstance(docker_command, str):  # Only process if it's a string
            # find the exposed container port from the docker command
            match = re.search(r'action_execution_server\s+(\d+)', docker_command)
            if match:
                command_port = int(match.group(1))
                if start <= command_port <= end:
                    used_ports.add(command_port)
            
        # Get ports list, defaulting to empty list if not present
        ports = container.attrs.get("Ports", [])
        if isinstance(ports, list):  # Only process if it's a list
            for port in ports:
                if isinstance(port, dict):  # Only process if it's a dictionary
                    host_port = port.get("PublicPort")
                    if host_port:
                        try:
                            port_num = int(host_port)
                            if start <= port_num <= end:
                                used_ports.add(port_num)
                        except (ValueError, TypeError) as e:
                            logger.error(f"Error processing port {host_port}: {e}")
                            raise e
    return used_ports