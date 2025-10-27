# openhands_cli/settings/store.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp.mcp_config import MCPConfig
from openhands_cli.llm_utils import get_llm_metadata
from openhands_cli.locations import (
    AGENT_SETTINGS_PATH,
    MCP_CONFIG_FILE,
    PERSISTENCE_DIR,
    WORK_DIR,
)
from prompt_toolkit import HTML, print_formatted_text

from openhands.sdk import Agent, AgentContext, LocalFileStore
from openhands.sdk.context.condenser import LLMSummarizingCondenser
from openhands.tools.preset.default import get_default_tools


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""

    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=PERSISTENCE_DIR)

    def load_mcp_configuration(self) -> dict[str, Any]:
        try:
            mcp_config_path = Path(self.file_store.root) / MCP_CONFIG_FILE
            mcp_config = MCPConfig.from_file(mcp_config_path)
            return mcp_config.to_dict()['mcpServers']
        except Exception:
            return {}

    def load(self, session_id: str | None = None) -> Agent | None:
        try:
            str_spec = self.file_store.read(AGENT_SETTINGS_PATH)
            agent = Agent.model_validate_json(str_spec)

            # Update tools with most recent working directory
            updated_tools = get_default_tools(enable_browser=False)

            agent_context = AgentContext(
                system_message_suffix=f'You current working directory is: {WORK_DIR}',
            )

            additional_mcp_config = self.load_mcp_configuration()
            mcp_config: dict = agent.mcp_config.copy().get('mcpServers', {})
            mcp_config.update(additional_mcp_config)

            # Update LLM metadata with current information
            agent_llm_metadata = get_llm_metadata(
                model_name=agent.llm.model, llm_type='agent', session_id=session_id
            )
            updated_llm = agent.llm.model_copy(update={'metadata': agent_llm_metadata})

            condenser_updates = {}
            if agent.condenser and isinstance(agent.condenser, LLMSummarizingCondenser):
                condenser_updates['llm'] = agent.condenser.llm.model_copy(
                    update={
                        'metadata': get_llm_metadata(
                            model_name=agent.condenser.llm.model,
                            llm_type='condenser',
                            session_id=session_id,
                        )
                    }
                )

            agent = agent.model_copy(
                update={
                    'llm': updated_llm,
                    'tools': updated_tools,
                    'mcp_config': {'mcpServers': mcp_config} if mcp_config else {},
                    'agent_context': agent_context,
                    'condenser': agent.condenser.model_copy(update=condenser_updates)
                    if agent.condenser
                    else None,
                }
            )

            return agent
        except FileNotFoundError:
            return None
        except Exception:
            print_formatted_text(
                HTML('\n<red>Agent configuration file is corrupted!</red>')
            )
            return None

    def save(self, agent: Agent) -> None:
        serialized_spec = agent.model_dump_json(context={'expose_secrets': True})
        self.file_store.write(AGENT_SETTINGS_PATH, serialized_spec)
