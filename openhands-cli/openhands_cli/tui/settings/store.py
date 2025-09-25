# openhands_cli/settings/store.py
from __future__ import annotations
import os
from openhands.sdk import LocalFileStore, Agent
from openhands.sdk.preset.default import get_default_tools
from openhands_cli.locations import AGENT_SETTINGS_PATH, MCP_CONFIG_PATH, PERSISTENCE_DIR, WORK_DIR
from openhands_cli.user_actions.mcp_action import load_mcp_config
from prompt_toolkit import HTML, print_formatted_text


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=PERSISTENCE_DIR)

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

            mcp_config: dict = load_mcp_config(MCP_CONFIG_PATH)
            existing_config = agent.mcp_config.copy()
            mcp_config.update(existing_config)


            agent = agent.model_copy(update={
                "tools": updated_tools,
                "mcp_config": mcp_config
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

