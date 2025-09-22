# openhands_cli/settings/store.py
from __future__ import annotations
from openhands.sdk import LocalFileStore, Agent
from openhands_cli.locations import AGENT_SETTINGS_PATH, WORKING_DIR
from prompt_toolkit import HTML, print_formatted_text


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=WORKING_DIR)

    def load(self) -> Agent | None:
        try:
            str_spec = self.file_store.read(AGENT_SETTINGS_PATH)
            return Agent.model_validate_json(str_spec)
        except FileNotFoundError:
            return None
        except Exception:
            print_formatted_text(HTML("\n<red>Agent configuration file is corrupted!</red>"))
            return None

    def save(self, agent: Agent) -> None:
        serialized_spec = agent.model_dump_json(context={"expose_secrets": True})
        self.file_store.write(AGENT_SETTINGS_PATH, serialized_spec)

