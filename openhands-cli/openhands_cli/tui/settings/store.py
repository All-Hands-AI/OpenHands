# openhands_cli/settings/store.py
from __future__ import annotations
from pathlib import Path
from openhands.sdk import LocalFileStore, Agent
from openhands.sdk import LocalFileStore, Agent, AgentContext
from openhands.sdk.preset.default import get_default_tools
from openhands_cli.locations import AGENT_SETTINGS_PATH, MCP_CONFIG_FILE, PERSISTENCE_DIR, WORK_DIR
from prompt_toolkit import HTML, print_formatted_text
from fastmcp.mcp_config import MCPConfig


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=PERSISTENCE_DIR)

    def load_mcp_configuration(self):
        """Load MCP configuration from ~/.openhands/mcp.json."""
        try:
            # Use the file store to get the full path and read the file
            mcp_config_path = Path(self.file_store.root) / MCP_CONFIG_FILE
            mcp_config = MCPConfig.from_file(mcp_config_path)
            return mcp_config.to_dict()['mcpServers']
        except FileNotFoundError:
            # File doesn't exist, that's okay - return empty config
            return {}
        except ValueError as e:
            print_formatted_text(HTML(f"\n<red>Error loading MCP servers from ~/.openhands/{MCP_CONFIG_FILE}: {e}!</red>"))
            return {}
        except Exception as e:
            print_formatted_text(HTML(f"\n<red>Unexpected error loading MCP configuration from ~/.openhands/{MCP_CONFIG_FILE}: {e}!</red>"))
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

            agent_context = AgentContext(
                system_message_suffix=f"You current working directory is: {WORK_DIR}",
            )


            mcp_config = self.load_mcp_configuration()
            existing_config = agent.mcp_config.copy().get('mcpServers', {})
            mcp_config.update(existing_config)

            agent = agent.model_copy(update={
                "tools": updated_tools,
                "mcp_config": {'mcpServers': mcp_config} if mcp_config else {},
                "agent_context": agent_context
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

