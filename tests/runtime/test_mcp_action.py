"""Bash-related tests for the DockerRuntime, which connects to the ActionExecutor running in the sandbox."""

import json
import os

import pytest
from conftest import (
    _load_runtime,
)

import openhands
from openhands.core.config import MCPConfig
from openhands.core.config.mcp_config import MCPStdioServerConfig
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
