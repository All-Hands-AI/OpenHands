"""Image-related tests for the EventStreamRuntime, which connects to the RuntimeClient running in the sandbox."""

import asyncio

import pytest
from conftest import _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction

# ============================================================================================================================
# Image-specific tests
# ============================================================================================================================


@pytest.mark.asyncio
async def test_bash_python_version(temp_dir, box_class, container_image):
    """Make sure Python is available in bash."""
    if container_image not in [
        'python:3.11-bookworm',
        'nikolaik/python-nodejs:python3.11-nodejs22',
    ]:
        pytest.skip('This test is only for python-related images')

    runtime = await _load_runtime(temp_dir, box_class, container_image=container_image)

    action = CmdRunAction(command='which python')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action = CmdRunAction(command='python --version')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0
    assert 'Python 3.11' in obs.content  # Check for specific version

    action = CmdRunAction(command='pip --version')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0
    assert 'pip' in obs.content  # Check that pip is available

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_nodejs_22_version(temp_dir, box_class, container_image):
    """Make sure Node.js is available in bash."""
    if container_image not in [
        'node:22-bookworm',
        'nikolaik/python-nodejs:python3.11-nodejs22',
    ]:
        pytest.skip('This test is only for nodejs-related images')

    runtime = await _load_runtime(temp_dir, box_class, container_image=container_image)

    action = CmdRunAction(command='node --version')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0
    assert 'v22' in obs.content  # Check for specific version

    await runtime.close()
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_go_version(temp_dir, box_class, container_image):
    """Make sure Go is available in bash."""
    if container_image not in [
        'golang:1.23-bookworm',
    ]:
        pytest.skip('This test is only for go-related images')

    runtime = await _load_runtime(temp_dir, box_class, container_image=container_image)

    action = CmdRunAction(command='go version')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = await runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0
    assert 'go1.23' in obs.content  # Check for specific version

    await runtime.close()
    await asyncio.sleep(1)
