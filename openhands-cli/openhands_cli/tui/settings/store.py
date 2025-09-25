# openhands_cli/settings/store.py
from __future__ import annotations
from pathlib import Path
from openhands.sdk import LocalFileStore, Agent
from openhands.sdk.preset.default import get_default_tools
from openhands_cli.locations import AGENT_SETTINGS_PATH, MCP_CONFIG_PATH, PERSISTENCE_DIR, WORK_DIR
from prompt_toolkit import HTML, print_formatted_text
from fastmcp.mcp_config import MCPConfig


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=PERSISTENCE_DIR)

    def load_mcp_configuration(self):
        try:
            mcp_json_location = self.file_store.read(MCP_CONFIG_PATH)
        except FileNotFoundError:
            return {}


        try:
            mcp_config = MCPConfig.from_file(Path(mcp_json_location))
            return mcp_config.to_dict()['mcpServers']
        except ValueError as e:
            return {}

    def load(self) -> Agent | None:
        try:
            str_spec = self.file_store.read(AGENT_SETTINGS_PATH)
            agent = Agent.model_validate_json(str_spec)

            # Update tools with most recent working directory
            updated_tools = get_default_tools(
                working_dir=WORK_DIR,
                persistence_dir=PERSISTENCE_DIR,
                enable_browser=False
            )

            mcp_config = self.load_mcp_configuration()
            existing_config = agent.mcp_config.copy().get('mcpServers', {})
            mcp_config.update(existing_config)


            agent = agent.model_copy(update={
                "tools": updated_tools,
                "mcp_config": {'mcpServers': mcp_config} if mcp_config else {}
            })

            return agent
        except FileNotFoundError:
            return None
        except Exception:
            print_formatted_text(HTML("\n<red>Agent configuration file is corrupted!</red>"))
            return None

    def save(self, agent: Agent) -> None:
        serialized_spec = agent.model_dump_json(context={"expose_secrets": True})
        self.file_store.write(AGENT_SETTINGS_PATH, serialized_spec)

