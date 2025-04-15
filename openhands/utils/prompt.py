import os
from dataclasses import dataclass, field
from itertools import islice

from jinja2 import Template

from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.message import Message, TextContent
from openhands.events.observation.agent import MicroagentKnowledge


@dataclass
class RuntimeInfo:
    date: str
    available_hosts: dict[str, int] = field(default_factory=dict)
    additional_agent_instructions: str = ''


@dataclass
class RepositoryInfo:
    """Information about a GitHub repository that has been cloned."""

    repo_name: str | None = None
    repo_directory: str | None = None


class PromptManager:
    """
    Manages prompt templates and includes information from the user's workspace micro-agents and global micro-agents.

    This class is dedicated to loading and rendering prompts (system prompt, user prompt).

    Attributes:
        prompt_dir: Directory containing prompt templates.
    """

    def __init__(self, prompt_dir: str, config: AgentConfig):
        """
        Initializes the PromptManager.

        Args:
            prompt_dir: Directory containing prompt templates.
            config: The agent configuration object.
        """
        self.prompt_dir: str = prompt_dir
        self.config: AgentConfig = config

        # Load the correct system prompt based on the config
        if self.config.enable_llm_diff:
            system_template_name = 'system_prompt_llm_diff'
        else:
            system_template_name = 'system_prompt'
        self.system_template: Template = self._load_template(system_template_name)

        # Load other templates
        self.user_template: Template = self._load_template('user_prompt')
        self.additional_info_template: Template = self._load_template('additional_info')
        self.microagent_info_template: Template = self._load_template('microagent_info')

    def _load_template(self, template_name: str) -> Template:
        if self.prompt_dir is None:
            raise ValueError('Prompt directory is not set')
        template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f'Prompt file {template_path} not found')
        with open(template_path, 'r') as file:
            return Template(file.read())

    def get_system_message(self) -> str:
        return self.system_template.render().strip()

    def get_example_user_message(self) -> str:
        """This is the initial user message provided to the agent
        before *actual* user instructions are provided.

        It is used to provide a demonstration of how the agent
        should behave in order to solve the user's task. And it may
        optionally contain some additional context about the user's task.
        These additional context will convert the current generic agent
        into a more specialized agent that is tailored to the user's task.
        """

        return self.user_template.render().strip()

    def add_examples_to_initial_message(self, message: Message) -> None:
        """Add example_message to the first user message."""
        example_message = self.get_example_user_message() or None

        # Insert it at the start of the TextContent list
        if example_message:
            message.content.insert(0, TextContent(text=example_message))

    def build_workspace_context(
        self,
        repository_info: RepositoryInfo | None,
        runtime_info: RuntimeInfo | None,
        repo_instructions: str = '',
    ) -> str:
        """Renders the additional info template with the stored repository/runtime info."""
        return self.additional_info_template.render(
            repository_info=repository_info,
            repository_instructions=repo_instructions,
            runtime_info=runtime_info,
        ).strip()

    def build_microagent_info(
        self,
        triggered_agents: list[MicroagentKnowledge],
    ) -> str:
        """Renders the microagent info template with the triggered agents.

        Args:
            triggered_agents: A list of MicroagentKnowledge objects containing information
                              about triggered microagents.
        """
        return self.microagent_info_template.render(
            triggered_agents=triggered_agents
        ).strip()

    def add_turns_left_reminder(self, messages: list[Message], state: State) -> None:
        latest_user_message = next(
            islice(
                (
                    m
                    for m in reversed(messages)
                    if m.role == 'user'
                    and any(isinstance(c, TextContent) for c in m.content)
                ),
                1,
            ),
            None,
        )
        if latest_user_message:
            reminder_text = ''
            # Every 10 steps
            if state.iteration % 10 == 0:
                reminder_text += """\n\n## WORKFLOW REMINDER: General Workflow Guidance
*   Follow the **Problem Solving Workflow** outlined before.
*   Prioritize understanding the problem, exploring the code, planning your fix, implementing it carefully, and **thoroughly testing** according to the **Mandatory Testing Procedure**.
*   Consider trade-offs between different solutions. The goal is a **robust change that makes the relevant tests pass.** Quality, correctness, and reliability are key.
*   Actively practice defensive programming: anticipate and handle potential edge cases, unexpected inputs, and different ways the affected code might be called **to ensure the fix works reliably and allows relevant tests to pass.** Analyze the potential impact on other parts of the codebase.
*   IMPORTANT: Your solution will be tested by additional hidden tests, so do not assume the task is complete just because visible tests pass; refine the solution until you are confident that it is robust and comprehensive. 

## Final Note
Be thorough in your exploration, testing, and reasoning. It's fine if your thinking process is lengthy - quality and completeness are more important than brevity.

---
"""
            reminder_text +=f"ENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task. When finished reply with <finish></finish>."
            latest_user_message.content.append(TextContent(text=reminder_text))
