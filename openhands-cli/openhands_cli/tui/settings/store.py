# openhands_cli/settings/store.py
from __future__ import annotations
import os
from openhands.sdk import LocalFileStore, Agent
from openhands_cli.locations import AGENT_SETTINGS_PATH, PERSISTENCE_DIR, WORK_DIR
from prompt_toolkit import HTML, print_formatted_text


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=PERSISTENCE_DIR)

    def load(self) -> Agent | None:
        try:
            str_spec = self.file_store.read(AGENT_SETTINGS_PATH)
            agent = Agent.model_validate_json(str_spec)

            # Fix bash tool spec to use current directory instead of hardcoded path
            if not agent.tools:
                return agent

            updated_tools = []
            for tool_spec in agent.tools:
                if tool_spec.name == "BashTool":
                    # Update the working_dir parameter to use current directory
                    updated_params = tool_spec.params or {}
                    updated_params["working_dir"] = WORK_DIR
                    updated_tool_spec = tool_spec.model_copy(update={"params": updated_params})
                    updated_tools.append(updated_tool_spec)
                else:
                    updated_tools.append(tool_spec)
            agent = agent.model_copy(update={"tools": updated_tools})

            return agent
        except FileNotFoundError:
            return None
        except Exception:
            print_formatted_text(HTML("\n<red>Agent configuration file is corrupted!</red>"))
            return None

    def save(self, agent: Agent) -> None:
        serialized_spec = agent.model_dump_json(context={"expose_secrets": True})
        self.file_store.write(AGENT_SETTINGS_PATH, serialized_spec)

