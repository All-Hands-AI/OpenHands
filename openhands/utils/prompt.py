import os
import re
from dataclasses import dataclass, field
from itertools import islice

from jinja2 import Template

from openhands.a2a.common.types import Artifact
from openhands.a2a.utils import convert_parts
from openhands.controller.state.state import State
from openhands.core.message import Message, TextContent
from openhands.events.observation.a2a import A2ASendTaskArtifactObservation
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

    def __init__(
        self,
        prompt_dir: str,
    ):
        self.prompt_dir: str = prompt_dir
        self.system_template: Template = self._load_template('system_prompt')
        self.user_template: Template = self._load_template('user_prompt')
        self.additional_info_template: Template = self._load_template('additional_info')
        self.microagent_info_template: Template = self._load_template('microagent_info')
        self.a2a_info_template: Template = self._load_template('a2a_info')
        self.chat_mode_template: Template = self._load_template('chat_mode_prompt')
        self.followup_mode_template: Template = self._load_template(
            'followup_mode_prompt'
        )
        self.system_prompt: str | None = None
        self.user_prompt: str | None = None

    def _load_template(self, template_name: str) -> Template:
        if self.prompt_dir is None:
            raise ValueError('Prompt directory is not set')
        template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
        if not os.path.exists(template_path):
            # raise FileNotFoundError(f'Prompt file {template_path} not found')
            return Template('')
        with open(template_path, 'r') as file:
            return Template(file.read())

    def set_system_message(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt

    def set_user_message(self, user_prompt: str) -> None:
        self.user_prompt = user_prompt

    def get_system_message(self, **kwargs) -> str:
        # **kwargs is used to pass additional context to the system prompt, such as current date, ...
        final_system_prompt = self.system_template.render(**kwargs).strip()
        if self.system_prompt:
            agent_infos_prompt = ''
            agent_infos_prompt_match = re.search(
                r'<A2A_INFO>(.*?)</A2A_INFO>', final_system_prompt, re.DOTALL
            )
            if agent_infos_prompt_match:
                agent_infos_prompt = agent_infos_prompt_match.group(1)
            final_system_prompt = self.system_prompt + '\n' + agent_infos_prompt
        return final_system_prompt

    def get_chat_mode_message(self, **kwargs) -> str:
        return self.chat_mode_template.render(**kwargs).strip()

    def get_followup_mode_message(self, **kwargs) -> str:
        return self.followup_mode_template.render(**kwargs).strip()

    def get_example_user_message(self) -> str:
        """This is the initial user message provided to the agent
        before *actual* user instructions are provided.

        It is used to provide a demonstration of how the agent
        should behave in order to solve the user's task. And it may
        optionally contain some additional context about the user's task.
        These additional context will convert the current generic agent
        into a more specialized agent that is tailored to the user's task.
        """

        if self.user_prompt:
            return self.user_prompt
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

    def build_a2a_info(
        self,
        agent_artifact_observation: A2ASendTaskArtifactObservation,
    ) -> str:
        """Renders the a2a info template with the triggered agents."""

        artifact = Artifact(
            **agent_artifact_observation.task_artifact_event['artifact']
        )
        parts = artifact.parts
        converted_parts = convert_parts(parts)
        text = '\n'.join(converted_parts)
        art_obs = {'agent_name': agent_artifact_observation.agent_name, 'content': text}
        return self.a2a_info_template.render(agent_artifact_observation=art_obs).strip()

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
            reminder_text = f'\n\nENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task. When finished reply with <finish></finish>.'
            latest_user_message.content.append(TextContent(text=reminder_text))
