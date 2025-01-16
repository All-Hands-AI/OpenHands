import os
from itertools import islice

from jinja2 import Template

from openhands.controller.state.state import State
from openhands.core.message import Message, TextContent
from openhands.utils.microagent import MicroAgent


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
        self.prompt_dir: str = prompt_dir

        self.system_template: Template = self._load_template('system_prompt')
        self.user_template: Template = self._load_template('user_prompt')
        self.microagents: dict = {}

        microagent_files = []
        if microagent_dir:
            microagent_files = [
                os.path.join(microagent_dir, f)
                for f in os.listdir(microagent_dir)
                if f.endswith('.md')
            ]
        for microagent_file in microagent_files:
            microagent = MicroAgent(path=microagent_file)
            if (
                disabled_microagents is None
                or microagent.name not in disabled_microagents
            ):
                self.microagents[microagent.name] = microagent

    def load_microagent_files(self, microagent_files: list[str]):
        for microagent_file in microagent_files:
            microagent = MicroAgent(content=microagent_file)
            self.microagents[microagent.name] = microagent

    def _load_template(self, template_name: str) -> Template:
        if self.prompt_dir is None:
            raise ValueError('Prompt directory is not set')
        template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f'Prompt file {template_path} not found')
        with open(template_path, 'r') as file:
            return Template(file.read())

    def get_system_message(self) -> str:
        repo_instructions = ''
        for microagent in self.microagents.values():
            # We assume these are the repo instructions
            if len(microagent.triggers) == 0:
                if repo_instructions:
                    repo_instructions += '\n\n'
                repo_instructions += microagent.content
        return self.system_template.render(repo_instructions=repo_instructions).strip()

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
        for microagent in self.microagents.values():
            trigger = microagent.get_trigger(message_content)
            if trigger:
                micro_text = f'<extra_info>\nThe following information has been included based on a keyword match for "{trigger}". It may or may not be relevant to the user\'s request.'
                micro_text += '\n\n' + microagent.content
                micro_text += '\n</extra_info>'
                message.content.append(TextContent(text=micro_text))

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
