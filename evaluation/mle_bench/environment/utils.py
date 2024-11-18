import json
import os
import tarfile
import uuid
from pathlib import Path
from typing import Optional

import docker
from docker import DockerClient
from docker.models.containers import Container
from mlebench.registry import Competition
from mlebench.utils import get_logger, get_timestamp

logger = get_logger(__name__)


def parse_container_config(raw_config: dict) -> dict:
    """
    Parses raw configuration for container.
    Mostly necessary for handling GPU configuration.
    """
    new_config = {k: v for k, v in raw_config.items() if k != 'gpus'}

    # handle GPU configuration
    if 'gpus' in raw_config and raw_config['gpus'] != 0:
        gpu_count = raw_config['gpus']
        new_config['device_requests'] = [
            docker.types.DeviceRequest(count=gpu_count, capabilities=[['gpu']])
        ]

    # cast nano_cpus to int
    new_config['nano_cpus'] = (
        int(new_config['nano_cpus']) if 'nano_cpus' in new_config else None
    )

    return new_config


def reconcile_args(
    config_args: Optional[str] = None, dict_args: Optional[dict] = None
) -> dict:
    """
    Reconcile the args specified by config file and args specified in a dictionary

    In case of duplicates, config file's args take precedence
    """
    reconciled_args = {}
    if dict_args:
        reconciled_args.update(dict_args)
    if config_args:
        reconciled_args = json.loads(config_args)
    return reconciled_args


def extract_from_container_sysbox(
    container: Container, container_file_path: str, local_dir: Path
):
    """
    Extracts a file or directory from a container to a specified local directory.
    """
    try:
        # Get the directory and base name of the file or directory to extract
        dir_name = os.path.dirname(container_file_path)
        base_name = os.path.basename(container_file_path)

        # Construct the tar command to tar the base_name and output to stdout
        command = ['tar', 'cf', '-', '-C', dir_name, base_name]
        exec_result = container.exec_run(
            cmd=command, stdout=True, stderr=True, stream=True
        )

        # Create a file-like object from the output generator
        import io

        class StreamWrapper(io.RawIOBase):
            def __init__(self, generator):
                self.generator = generator
                self.leftover = b''

            def readinto(self, b):
                try:
                    chunk = next(self.generator)
                except StopIteration:
                    return 0  # EOF
                n = len(chunk)
                b[:n] = chunk
                return n

        stream_wrapper = StreamWrapper(exec_result.output)

        # Extract the tar stream
        with tarfile.open(fileobj=stream_wrapper, mode='r|') as tar:
            tar.extractall(path=local_dir)

    except FileNotFoundError:
        logger.warning(f'Nothing found in container at {container_file_path}.')
    except Exception as e:
        logger.error(f'Error extracting output file: {e}')


def extract_from_container(
    container: Container, container_file_path: str, local_dir: Path
):
    """
    Extracts a file or directory from a container to a specified local directory.
    """
    try:
        stream, _ = container.get_archive(container_file_path)
        tmp_tar_path = local_dir / 'tmp.tar'

        with open(tmp_tar_path, 'wb') as f:
            for chunk in stream:
                f.write(chunk)

        # extracts the original file(s) from the tar file
        with tarfile.open(tmp_tar_path, 'r') as tar:
            tar.extractall(path=local_dir)

        tmp_tar_path.unlink()
    except FileNotFoundError:
        logger.warning(f'Nothing found in container at {container_file_path}.')
    except Exception as e:
        logger.error(f'Error extracting output file: {e}')


def create_competition_container(
    client: DockerClient,
    competition: Competition,
    container_config: dict,
    volumes_config: dict,
    env_vars: dict,
    container_image: str = 'mlebench-env',
    privileged: bool = False,
) -> Container:
    """
    Creates a container for the given competition, mounting the competition data and agent volumes.

    Args:
        client: Docker client to interact with Docker.
        competition: Competition object
        container_config: Docker configuration for the container.
        volumes_config: Docker bind-mount configuration for the container.
        env_vars: Environment variables to pass to the container.
        container_image: Docker image to use for the container.
        privileged: Whether to run the container in privileged mode. Default is False.

    Returns:
        Created Docker container.
    """
    unique_id = str(uuid.uuid4().hex)
    timestamp = get_timestamp()

    container = client.containers.create(
        image=container_image,
        name=f'competition-{competition.id}-{timestamp}-{unique_id}',
        detach=True,
        **parse_container_config(container_config),
        volumes=volumes_config,
        environment=env_vars,
        privileged=privileged,
    )

    logger.info(f'Container created: {container.name}')
    return container
