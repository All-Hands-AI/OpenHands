# openhands_cli/settings/store.py
from __future__ import annotations
import os
from openhands_cli.locations import AGENT_SETTINGS_PATH, PERSISTENCE_DIR, WORK_DIR


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        from openhands.sdk import LocalFileStore
        self.file_store = LocalFileStore(root=PERSISTENCE_DIR)

    def load(self):
        from openhands.sdk import Agent
        from openhands.sdk.preset.default import get_default_tools
        
        try:
            str_spec = self.file_store.read(AGENT_SETTINGS_PATH)
            agent = Agent.model_validate_json(str_spec)

            # Update tools with most recent working directory
            updated_tools = get_default_tools(
                working_dir=WORK_DIR,
                persistence_dir=PERSISTENCE_DIR,
                enable_browser=False
            )
            agent = agent.model_copy(update={"tools": updated_tools})

            return agent
        except FileNotFoundError:
            return None
        except Exception:
            from prompt_toolkit import HTML, print_formatted_text
            print_formatted_text(HTML("\n<red>Agent configuration file is corrupted!</red>"))
            return None

    def save(self, agent) -> None:
        serialized_spec = agent.model_dump_json(context={"expose_secrets": True})
        self.file_store.write(AGENT_SETTINGS_PATH, serialized_spec)

