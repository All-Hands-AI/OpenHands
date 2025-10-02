"""Parametrized tests for MCP configuration screen functionality."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from openhands_cli.locations import MCP_CONFIG_FILE
from openhands_cli.tui.settings.mcp_screen import MCPScreen

from openhands.sdk import LLM, Agent


@pytest.fixture
def persistence_dir(tmp_path, monkeypatch):
    """Patch PERSISTENCE_DIR to tmp and return the directory Path."""
    monkeypatch.setattr(
        'openhands_cli.tui.settings.mcp_screen.PERSISTENCE_DIR',
        str(tmp_path),
        raising=True,
    )
    return tmp_path


def _create_agent(mcp_config=None) -> Agent:
    if mcp_config is None:
        mcp_config = {}
    return Agent(
        llm=LLM(model='test-model', api_key='test-key', service_id='test-service'),
        tools=[],
        mcp_config=mcp_config,
    )


def _maybe_write_mcp_file(dirpath: Path, file_content):
    """Write mcp.json if file_content is provided.

    file_content:
      - None     -> do not create file (missing)
      - "INVALID"-> write invalid JSON
      - dict     -> dump as JSON
    """
    if file_content is None:
        return
    cfg_path = dirpath / MCP_CONFIG_FILE
    if file_content == 'INVALID':
        cfg_path.write_text('{"invalid": json content}')
    else:
        cfg_path.write_text(json.dumps(file_content))


# Shared "always expected" help text snippets
ALWAYS_EXPECTED = [
    'MCP (Model Context Protocol) Configuration',
    'To get started:',
    '~/.openhands/mcp.json',
    'https://gofastmcp.com/clients/client#configuration-format',
    'Restart your OpenHands session',
]


CASES = [
    # Agent has an existing server; should list "Current Agent MCP Servers"
    dict(
        id='agent_has_existing',
        agent_mcp={
            'mcpServers': {
                'existing_server': {
                    'command': 'python',
                    'args': ['-m', 'existing_server'],
                }
            }
        },
        file_content=None,  # no incoming file
        expected=[
            'Current Agent MCP Servers:',
            'existing_server',
        ],
        unexpected=[],
    ),
    # Agent has none; should show "None configured on the current agent"
    dict(
        id='agent_has_none',
        agent_mcp={},
        file_content=None,
        expected=[
            'Current Agent MCP Servers:',
            'None configured on the current agent',
        ],
        unexpected=[],
    ),
    # New servers present only in mcp.json
    dict(
        id='new_servers_on_restart',
        agent_mcp={},
        file_content={
            'mcpServers': {
                'fetch': {'command': 'uvx', 'args': ['mcp-server-fetch']},
                'notion': {'url': 'https://mcp.notion.com/mcp', 'auth': 'oauth'},
            }
        },
        expected=[
            'Incoming Servers on Restart',
            'New servers (will be added):',
            'fetch',
            'notion',
        ],
        unexpected=[],
    ),
    # Overriding/updating servers present in both agent and mcp.json (but different config)
    dict(
        id='overriding_servers_on_restart',
        agent_mcp={
            'mcpServers': {
                'fetch': {'command': 'python', 'args': ['-m', 'old_fetch_server']}
            }
        },
        file_content={
            'mcpServers': {'fetch': {'command': 'uvx', 'args': ['mcp-server-fetch']}}
        },
        expected=[
            'Incoming Servers on Restart',
            'Updated servers (configuration will change):',
            'fetch',
            'Current:',
            'Incoming:',
        ],
        unexpected=[],
    ),
    # All servers already synced (matching config)
    dict(
        id='already_synced',
        agent_mcp={
            'mcpServers': {
                'fetch': {
                    'command': 'uvx',
                    'args': ['mcp-server-fetch'],
                    'env': {},
                    'transport': 'stdio',
                }
            }
        },
        file_content={
            'mcpServers': {'fetch': {'command': 'uvx', 'args': ['mcp-server-fetch']}}
        },
        expected=[
            'Incoming Servers on Restart',
            'All configured servers match the current agent configuration',
        ],
        unexpected=[],
    ),
    # Invalid JSON file handling
    dict(
        id='invalid_json_file',
        agent_mcp={},
        file_content='INVALID',
        expected=[
            'Invalid MCP configuration file',
            'Please check your configuration file format',
        ],
        unexpected=[],
    ),
    # Missing JSON file handling
    dict(
        id='missing_json_file',
        agent_mcp={},
        file_content=None,  # explicitly missing
        expected=[
            'Configuration file not found',
            'No incoming servers detected for next restart',
        ],
        unexpected=[],
    ),
]


@pytest.mark.parametrize('case', CASES, ids=[c['id'] for c in CASES])
@patch('openhands_cli.tui.settings.mcp_screen.print_formatted_text')
def test_display_mcp_info_parametrized(mock_print, case, persistence_dir):
    """Table-driven test for MCPScreen.display_mcp_info covering all scenarios."""
    # Arrange
    agent = _create_agent(case['agent_mcp'])
    _maybe_write_mcp_file(persistence_dir, case['file_content'])
    screen = MCPScreen()

    # Act
    screen.display_mcp_info(agent)

    # Gather output
    all_calls = [str(call_args) for call_args in mock_print.call_args_list]
    content = ' '.join(all_calls)

    # Invariants: help instructions should always be present
    for snippet in ALWAYS_EXPECTED:
        assert snippet in content, f'Missing help snippet: {snippet}'

    # Scenario-specific expectations
    for snippet in case['expected']:
        assert snippet in content, (
            f'Expected snippet not found for case {case["id"]}: {snippet}'
        )

    for snippet in case.get('unexpected', []):
        assert snippet not in content, (
            f'Unexpected snippet found for case {case["id"]}: {snippet}'
        )
