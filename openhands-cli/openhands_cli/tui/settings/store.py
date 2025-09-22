# openhands_cli/settings/store.py
from __future__ import annotations
import os
from openhands.sdk import LocalFileStore, Agent, ToolSpec
from openhands_cli.locations import AGENT_SETTINGS_PATH, PERSISTENCE_DIR, WORK_DIR
from prompt_toolkit import HTML, print_formatted_text


def create_default_tools(work_dir: str) -> list[ToolSpec]:
    """Create default tools with the specified working directory."""
    tools = []
    
    # Create BashTool with working_dir
    bash_tool = ToolSpec(
        name='BashTool',
        params={'working_dir': work_dir}
    )
    tools.append(bash_tool)
    
    # Create FileEditorTool with workspace_root
    file_editor_tool = ToolSpec(
        name='FileEditorTool', 
        params={'workspace_root': work_dir}
    )
    tools.append(file_editor_tool)
    
    # Create TaskTrackerTool with save_dir
    task_tracker_tool = ToolSpec(
        name='TaskTrackerTool',
        params={'save_dir': os.path.join(work_dir, '.openhands_tasks')}
    )
    tools.append(task_tracker_tool)
    
    return tools


class AgentStore:
    """Single source of truth for persisting/retrieving AgentSpec."""
    def __init__(self) -> None:
        self.file_store = LocalFileStore(root=PERSISTENCE_DIR)

    def load(self) -> Agent | None:
        try:
            str_spec = self.file_store.read(AGENT_SETTINGS_PATH)
            agent = Agent.model_validate_json(str_spec)

            # Override the entire tools field with new tools from create_default_tools
            updated_tools = create_default_tools(WORK_DIR)
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

