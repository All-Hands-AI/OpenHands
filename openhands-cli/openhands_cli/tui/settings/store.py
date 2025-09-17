# openhands_cli/settings/store.py
from __future__ import annotations
from openhands.sdk import LocalFileStore
from openhands.sdk.preset.default import get_default_agent_spec, AgentSpec
from openhands_cli.locations import AGENT_SPEC_PATH, WORKING_DIR
from prompt_toolkit import HTML, print_formatted_text

class AgentSpecStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=WORKING_DIR)

    def load(self) -> AgentSpec | None:
        try:
            str_spec = self.file_store.read(AGENT_SPEC_PATH)
            return AgentSpec.model_validate_json(str_spec)
        except FileNotFoundError:
            return None
        except Exception:
            print_formatted_text(HTML("\n<red>Agent configuration file is corrupted!</red>"))
            return None

    def save(self, spec: AgentSpec) -> None:
        self.file_store.write(AGENT_SPEC_PATH, spec.model_dump_json())


