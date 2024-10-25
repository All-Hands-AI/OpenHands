import os

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
        agent_skills_docs (str): Documentation of agent skills.
    """

    def __init__(
        self,
        prompt_dir: str,
        agent_skills_docs: str,
    ):
        self.prompt_dir: str = prompt_dir
        self.agent_skills_docs: str = agent_skills_docs

        self.system_template: Template = self._load_template('system_prompt')
        self.user_template: Template = self._load_template('user_prompt')
        self.microagents: dict = {}

        micro_agent_dir = os.path.join(prompt_dir, 'micro')
        micro_agent_files = [
            os.path.join(micro_agent_dir, f)
            for f in os.listdir(micro_agent_dir)
            if f.endswith('.md')
        ]
        for micro_agent_file in micro_agent_files:
            micro_agent = MicroAgent(micro_agent_file)
            self.microagents[micro_agent.name] = micro_agent

    def _load_template(self, template_name: str) -> Template:
        template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f'Prompt file {template_path} not found')
        with open(template_path, 'r') as file:
            return Template(file.read())

    def get_system_message(self) -> str:
        rendered = self.system_template.render(
            agent_skills_docs=self.agent_skills_docs,
        ).strip()
        return rendered

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

    def enhance_message(self, message: Message, state: State) -> None:
        """Enhance the user message with additional context.

        This method is used to enhance the user message with additional context
        about the user's task. The additional context will convert the current
        generic agent into a more specialized agent that is tailored to the user's task.
        """
        micro_agent_prompts = []
        for micro_agent in self.microagents.values():
            if micro_agent.should_trigger(message):
                micro_agent_prompts.append(micro_agent.content)
        if len(micro_agent_prompts) > 0:
            micro_text = "EXTRA INFO: the following information has been included based on a keyword match. It may or may not be relevant to the user's request.\n\n"
            for micro_agent_prompt in micro_agent_prompts:
                micro_text += micro_agent_prompt + '\n\n'
            message.content.append(TextContent(text=micro_text))
        reminder_text = f'ENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task. When finished reply with <finish></finish>.'
        message.content.append(TextContent(text=reminder_text))
