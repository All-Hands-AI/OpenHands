"""Bash-related tests for the DockerRuntime, which connects to the ActionExecutor running in the sandbox."""

import json
import os
import time

import docker
import pytest
from conftest import (
    _load_runtime,
)

import openhands
from openhands.core.config import MCPConfig
from openhands.core.config.mcp_config import MCPSSEServerConfig, MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction, MCPAction
from openhands.events.observation import CmdOutputObservation, MCPObservation

# ============================================================================================================================
# Bash-specific tests
# ============================================================================================================================


def test_default_activated_tools():
    project_root = os.path.dirname(openhands.__file__)
    mcp_config_path = os.path.join(project_root, 'runtime', 'mcp', 'config.json')
    assert os.path.exists(mcp_config_path), (
        f'MCP config file not found at {mcp_config_path}'
    )
    with open(mcp_config_path, 'r') as f:
        mcp_config = json.load(f)
    assert 'default' in mcp_config
    # no tools are always activated yet
    assert len(mcp_config['default']) == 0


@pytest.mark.asyncio
async def test_fetch_mcp_via_stdio(temp_dir, runtime_cls, run_as_openhands):
    mcp_stdio_server_config = MCPStdioServerConfig(
        name='fetch', command='uvx', args=['mcp-server-fetch']
    )
    override_mcp_config = MCPConfig(stdio_servers=[mcp_stdio_server_config])
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, override_mcp_config=override_mcp_config
    )

    # Test browser server
    action_cmd = CmdRunAction(command='python3 -m http.server 8000 > server.log 2>&1 &')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert '[1]' in obs.content

    action_cmd = CmdRunAction(command='sleep 3 && cat server.log')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    mcp_action = MCPAction(name='fetch', arguments={'url': 'http://localhost:8000'})
    obs = await runtime.call_tool_mcp(mcp_action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, MCPObservation), (
        'The observation should be a MCPObservation.'
    )

    result_json = json.loads(obs.content)
    assert not result_json['isError']
    assert len(result_json['content']) == 1
    assert result_json['content'][0]['type'] == 'text'
    assert (
        result_json['content'][0]['text']
        == 'Contents of http://localhost:8000/:\n---\n\n* <server.log>\n\n---'
    )

    runtime.close()


@pytest.mark.asyncio
async def test_filesystem_mcp_via_sse(temp_dir, runtime_cls, run_as_openhands):
    image_name = 'supercorp/supergateway'
    container_command_args = [
        '--stdio',
        'npx -y @modelcontextprotocol/server-filesystem /',
        '--port',
        '8000',
        '--baseUrl',
        'http://localhost:8000',
    ]

    client = docker.from_env()

    logger.info(
        f'Starting Docker container {image_name} with command: {" ".join(container_command_args)}',
        extra={'msg_type': 'ACTION'},
    )

    container = client.containers.run(
        image_name,
        command=container_command_args,
        ports={'8000/tcp': 8000},
        detach=True,
        auto_remove=True,
        stdin_open=True,
    )
    logger.info(f'Container {container.short_id} started.')

    from openhands.runtime.utils.log_streamer import LogStreamer

    log_streamer = LogStreamer(
        container,
        lambda level, msg: getattr(logger, level.lower())(
            f'[MCP server {container.short_id}] {msg}'
        ),
    )
    time.sleep(10)

    try:
        mcp_sse_server_config = MCPSSEServerConfig(
            url='http://localhost:8000/sse',
        )
        override_mcp_config = MCPConfig(sse_servers=[mcp_sse_server_config])
        runtime, config = _load_runtime(
            temp_dir,
            runtime_cls,
            run_as_openhands,
            override_mcp_config=override_mcp_config,
        )

        mcp_action = MCPAction(name='list_directory', arguments={'path': '.'})
        obs = await runtime.call_tool_mcp(mcp_action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, MCPObservation), (
            'The observation should be a MCPObservation.'
        )
        assert '[FILE] .dockerenv' in obs.content

    finally:
        logger.info(f'Stopping container {container.short_id}...')
        container.stop()
        logger.info(f'Container {container.short_id} stopped.')
        runtime.close()
        log_streamer.close()


@pytest.mark.asyncio
async def test_both_stdio_and_sse_mcp(temp_dir, runtime_cls, run_as_openhands):
    # Launch SSE server
    image_name = 'supercorp/supergateway'
    container_command_args = [
        '--stdio',
        'npx -y @modelcontextprotocol/server-filesystem /',
        '--port',
        '8000',
        '--baseUrl',
        'http://localhost:8000',
    ]

    client = docker.from_env()

    logger.info(
        f'Starting Docker container {image_name} with command: {" ".join(container_command_args)}',
        extra={'msg_type': 'ACTION'},
    )

    container = client.containers.run(
        image_name,
        command=container_command_args,
        ports={'8000/tcp': 8000},
        detach=True,
        auto_remove=True,
        stdin_open=True,
    )
    logger.info(f'Container {container.short_id} started.')

    from openhands.runtime.utils.log_streamer import LogStreamer

    log_streamer = LogStreamer(
        container,
        lambda level, msg: getattr(logger, level.lower())(
            f'[MCP server {container.short_id}] {msg}'
        ),
    )
    time.sleep(10)

    try:
        mcp_sse_server_config = MCPSSEServerConfig(
            url='http://localhost:8000/sse',
        )

        # Also add stdio server
        mcp_stdio_server_config = MCPStdioServerConfig(
            name='fetch', command='uvx', args=['mcp-server-fetch']
        )

        override_mcp_config = MCPConfig(
            sse_servers=[mcp_sse_server_config], stdio_servers=[mcp_stdio_server_config]
        )
        runtime, config = _load_runtime(
            temp_dir,
            runtime_cls,
            run_as_openhands,
            override_mcp_config=override_mcp_config,
        )

        # ======= Test SSE server =======
        mcp_action = MCPAction(name='list_directory', arguments={'path': '.'})
        obs = await runtime.call_tool_mcp(mcp_action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, MCPObservation), (
            'The observation should be a MCPObservation.'
        )
        assert '[FILE] .dockerenv' in obs.content

        # ======= Test stdio server =======
        # Test browser server
        action_cmd = CmdRunAction(
            command='python3 -m http.server 8000 > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert '[1]' in obs.content

        action_cmd = CmdRunAction(command='sleep 3 && cat server.log')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        mcp_action = MCPAction(name='fetch', arguments={'url': 'http://localhost:8000'})
        obs = await runtime.call_tool_mcp(mcp_action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, MCPObservation), (
            'The observation should be a MCPObservation.'
        )

        result_json = json.loads(obs.content)
        assert not result_json['isError']
        assert len(result_json['content']) == 1
        assert result_json['content'][0]['type'] == 'text'
        assert (
            result_json['content'][0]['text']
            == 'Contents of http://localhost:8000/:\n---\n\n* <server.log>\n\n---'
        )
    finally:
        logger.info(f'Stopping container {container.short_id}...')
        container.stop()
        logger.info(f'Container {container.short_id} stopped.')
        runtime.close()
        log_streamer.close()
