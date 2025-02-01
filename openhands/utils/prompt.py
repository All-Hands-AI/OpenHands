import os
from dataclasses import dataclass
from itertools import islice

from jinja2 import Template

from openhands.controller.state.state import State
from openhands.core.message import Message, TextContent
from openhands.microagent import (
    BaseMicroAgent,
    KnowledgeMicroAgent,
    RepoMicroAgent,
    load_microagents_from_dir,
)
from openhands.runtime.base import Runtime


@dataclass
class RuntimeInfo:
    available_hosts: dict[str, int]


@dataclass
class RepositoryInfo:
    """Information about a GitHub repository that has been cloned."""

    repo_name: str | None = None
    repo_directory: str | None = None


ADDITIONAL_INFO_TEMPLATE = Template(
    """
{% if repository_info %}
<REPOSITORY_INFO>
At the user's request, repository {{ repository_info.repo_name }} has been cloned to directory {{ repository_info.repo_directory }}.
</REPOSITORY_INFO>
{% endif %}
{% if repository_instructions -%}
<REPOSITORY_INSTRUCTIONS>
{{ repository_instructions }}
</REPOSITORY_INSTRUCTIONS>
{% endif %}
{% if runtime_info and runtime_info.available_hosts -%}
<RUNTIME_INFORMATION>
The user has access to the following hosts for accessing a web application,
each of which has a corresponding port:
{% for host, port in runtime_info.available_hosts.items() -%}
* {{ host }} (port {{ port }})
{% endfor %}
When starting a web server, use the corresponding ports. You should also
set any options to allow iframes and CORS requests, and allow the server to
be accessed from any host (e.g. 0.0.0.0).
</RUNTIME_INFORMATION>
{% endif %}
"""
)


class PromptManager:
    """
    Manages prompt templates and micro-agents for AI interactions.

    This class handles loading and rendering of system and user prompt templates,
    as well as loading micro-agent specifications. It provides methods to access
    rendered system and initial user messages for AI interactions.

    Attributes:
        prompt_dir (str): Directory containing prompt templates.
        microagent_dir (str): Directory containing microagent specifications.
        disabled_microagents (list[str] | None): List of microagents to disable. If None, all microagents are enabled.
    """

    def __init__(
        self,
        prompt_dir: str,
        microagent_dir: str | None = None,
        disabled_microagents: list[str] | None = None,
    ):
        self.disabled_microagents: list[str] = disabled_microagents or []
        self.prompt_dir: str = prompt_dir
        self.repository_info: RepositoryInfo | None = None
        self.system_template: Template = self._load_template('system_prompt')
        self.user_template: Template = self._load_template('user_prompt')
        self.runtime_info = RuntimeInfo(available_hosts={})

        self.knowledge_microagents: dict[str, KnowledgeMicroAgent] = {}
        self.repo_microagents: dict[str, RepoMicroAgent] = {}

        if microagent_dir:
            # This loads micro-agents from the microagent_dir
            # which is typically the OpenHands/microagents (i.e., the PUBLIC microagents)

            # Only load KnowledgeMicroAgents
            repo_microagents, knowledge_microagents, _ = load_microagents_from_dir(
                microagent_dir
            )
            assert all(
                isinstance(microagent, KnowledgeMicroAgent)
                for microagent in knowledge_microagents.values()
            )
            for name, microagent in knowledge_microagents.items():
                if name not in self.disabled_microagents:
                    self.knowledge_microagents[name] = microagent
            assert all(
                isinstance(microagent, RepoMicroAgent)
                for microagent in repo_microagents.values()
            )
            for name, microagent in repo_microagents.items():
                if name not in self.disabled_microagents:
                    self.repo_microagents[name] = microagent

    def load_microagents(self, microagents: list[BaseMicroAgent]):
        """Load microagents from a list of BaseMicroAgents.

        This is typically used when loading microagents from inside a repo.
        """
        # Only keep KnowledgeMicroAgents and RepoMicroAgents
        for microagent in microagents:
            if microagent.name in self.disabled_microagents:
                continue
            if isinstance(microagent, KnowledgeMicroAgent):
                self.knowledge_microagents[microagent.name] = microagent
            elif isinstance(microagent, RepoMicroAgent):
                self.repo_microagents[microagent.name] = microagent

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

    def set_runtime_info(self, runtime: Runtime):
        self.runtime_info.available_hosts = runtime.web_hosts

    def set_repository_info(
        self,
        repo_name: str,
        repo_directory: str,
    ) -> None:
        """Sets information about the GitHub repository that has been cloned.

        Args:
            repo_name: The name of the GitHub repository (e.g. 'owner/repo')
            repo_directory: The directory where the repository has been cloned
        """
        self.repository_info = RepositoryInfo(
            repo_name=repo_name, repo_directory=repo_directory
        )

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

    def enhance_message(self, message: Message) -> None:
        """Enhance the user message with additional context.

        This method is used to enhance the user message with additional context
        about the user's task. The additional context will convert the current
        generic agent into a more specialized agent that is tailored to the user's task.
        """
        if not message.content:
            return
        message_content = message.content[0].text
        for microagent in self.knowledge_microagents.values():
            trigger = microagent.match_trigger(message_content)
            if trigger:
                micro_text = f'<extra_info>\nThe following information has been included based on a keyword match for "{trigger}". It may or may not be relevant to the user\'s request.'
                micro_text += '\n\n' + microagent.content
                micro_text += '\n</extra_info>'
                message.content.append(TextContent(text=micro_text))

    def add_examples_to_initial_message(self, message: Message) -> None:
        """Add example_message to the first user message."""
        example_message = self.get_example_user_message() or None

        # Insert it at the start of the TextContent list
        if example_message:
            message.content.insert(0, TextContent(text=example_message))

    def add_info_to_initial_message(
        self,
        message: Message,
    ) -> None:
        """Adds information about the repository and runtime to the initial user message.

        Args:
            message: The initial user message to add information to.
        """
        repo_instructions = ''
        assert (
            len(self.repo_microagents) <= 1
        ), f'Expecting at most one repo microagent, but found {len(self.repo_microagents)}: {self.repo_microagents.keys()}'
        for microagent in self.repo_microagents.values():
            # We assume these are the repo instructions
            if repo_instructions:
                repo_instructions += '\n\n'
            repo_instructions += microagent.content

        additional_info = ADDITIONAL_INFO_TEMPLATE.render(
            repository_instructions=repo_instructions,
            repository_info=self.repository_info,
            runtime_info=self.runtime_info,
        ).strip()

        # Insert the new content at the start of the TextContent list
        if additional_info:
            message.content.insert(0, TextContent(text=additional_info))

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
