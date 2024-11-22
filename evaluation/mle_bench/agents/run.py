import logging
import time
from pathlib import Path

import docker
from docker.models.containers import Container
from dotenv import dotenv_values
from environment.utils import (
    create_competition_container,
    extract_from_container,
    extract_from_container_sysbox,
)
from mlebench.registry import Competition
from mlebench.utils import purple

from agents.registry import Agent

CONSTANTS = dotenv_values(Path(__file__).parent.resolve() / '.shared_env')


def save_output(container: Container, save_dir: Path, container_config: dict) -> Path:
    """
    Extracts the submission, logs, and code directories from the container

    and saves them to the specified directory.

    Args:
        container: The Docker container.
        save_dir: The directory where the output file will be saved.
        container_config: The container configuration.
    Returns:
        Path to the output directory.
    """
    if 'runtime' in container_config and container_config['runtime'] == 'sysbox-runc':
        extraction_fn = extract_from_container_sysbox
    else:
        extraction_fn = extract_from_container

    for dir_type in ['SUBMISSION_DIR', 'LOGS_DIR', 'CODE_DIR']:
        container_dir = CONSTANTS[dir_type]
        extraction_fn(container, container_dir, save_dir)

    return save_dir


def execute_agent(container: Container, agent: Agent, logger: logging.Logger):
    """
    Initiates the agent via its start script inside the container.
    """
    cmd = ['bash', f"{CONSTANTS['AGENT_DIR']}/start.sh"]

    if agent.kwargs_type == 'argparse':
        for key, value in agent.kwargs.items():
            cmd += [f'--{key}', str(value)]

    if agent.kwargs_type == 'omegaconf':
        cmd += [f'{key}={value}' for key, value in agent.kwargs.items()]

    logger.info('Running agent...')
    _exit_code, output = container.exec_run(cmd, stream=True, user='nonroot')

    for chunk in output:
        logger.info(f"[Container] {chunk.decode('utf-8').strip()}")


def clean_up(
    container: Container, logger: logging.Logger, retain: bool = False
) -> bool:
    """
    Stops and removes the container.

    Returns:
        True if successful, False otherwise.
    """
    logger.info(f'Cleaning up container: {container.name}')
    try:
        container.stop()
        if not retain:
            container.remove()
        logger.info(f'Container {container.name} stopped and removed.')
        return True
    except Exception as e:
        logger.error(
            f'Error cleaning up: {e}. You may wish to manually check the status of the {container.name} container.'
        )
        return False


def run_in_container(
    client: docker.DockerClient,
    competition: Competition,
    agent: Agent,
    image: str,
    container_config: dict,
    retain_container: bool,
    run_dir: Path,
    logger: logging.Logger,
) -> Path:
    """
    Runs environment containing the competition and agent for a set maximum amount of time.

    Args:
        client: Docker client.
        competition: The competition to run.
        agent: The agent to run.
        image: The Docker image to use. Assumes the image is built.
        container_config: Configuration for the Docker container.
        retain_container: Whether to retain the container after the run instead of removing it.
        run_dir: Path to the directory where all assets associated with the run are stored.
        logger: Logger for the run.

    Returns:
        Path to the output file.
    """
    volumes_config = {
        competition.public_dir.resolve().as_posix(): {
            'bind': '/home/data',
            'mode': 'ro',
        },
        competition.private_dir.resolve().as_posix(): {
            'bind': f'/private/data/{competition.id}/prepared/private/',
            'mode': 'ro',
        },
        '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'},
    }

    container = create_competition_container(
        client=client,
        competition=competition,
        container_config=container_config,
        volumes_config=volumes_config,
        env_vars={
            'COMPETITION_ID': competition.id,
            **agent.env_vars,
        },
        container_image=image,
        privileged=agent.privileged,
    )

    logger.info(purple(f'Run started: {run_dir}'))
    try:
        time_start = time.monotonic()
        container.start()
        exit_code, _ = container.exec_run(
            'timeout 60s sh -c "while ! curl -s http://localhost:5000/health > /dev/null; do sleep 1; done"',
        )

        if exit_code != 0:
            raise RuntimeError(
                'The grading server failed to start within 60 seconds. This is likely due to an error in `entrypoint.sh`; check the logs.'
            )

        execute_agent(container, agent, logger)
        save_output(container, run_dir, container_config)
        time_end = time.monotonic()
        logger.info(f'Run completed in {time_end - time_start:.2f} seconds.')
        return run_dir
    except Exception as e:
        raise e
    finally:
        clean_up(container, logger, retain_container)
