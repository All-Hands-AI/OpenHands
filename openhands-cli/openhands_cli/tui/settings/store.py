# openhands_cli/settings/store.py
from __future__ import annotations
import os
from openhands.sdk import LocalFileStore, Agent
from openhands.sdk.preset.default import get_default_tools
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

            # Override the entire tools field with new tools from create_default_tools
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
            print_formatted_text(HTML("\n<red>Agent configuration file is corrupted!</red>"))
            return None

    def save(self, agent: Agent) -> None:
        serialized_spec = agent.model_dump_json(context={"expose_secrets": True})
        self.file_store.write(AGENT_SETTINGS_PATH, serialized_spec)

