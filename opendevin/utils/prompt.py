import os

from jinja2 import Template


class PromptManager:
    """
    Manages prompt templates and micro-agents for AI interactions.

    This class handles loading and rendering of system and user prompt templates,
    as well as loading micro-agent specifications. It provides methods to access
    rendered system and initial user messages for AI interactions.

    Attributes:
        prompt_dir (str): Directory containing prompt templates.
        agent_skills_docs (str): Documentation of agent skills.
        micro_agent (str | None): Content of the micro-agent definition file, if specified.
    """

    def __init__(
        self,
        prompt_dir: str,
        agent_skills_docs: str,
        micro_agent_name: str | None = None,
    ):
        self.prompt_dir: str = prompt_dir
        self.agent_skills_docs: str = agent_skills_docs

        self.system_template: Template = self._load_template('system_prompt')
        self.user_template: Template = self._load_template('user_prompt')
        self.micro_agent: str | None = (
            self._load_micro_agent(micro_agent_name) if micro_agent_name else None
        )

    def _load_template(self, template_name: str) -> Template:
        template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f'Prompt file {template_path} not found')
        with open(template_path, 'r') as file:
            return Template(file.read())

    def _load_micro_agent(self, micro_agent_name: str) -> str:
        micro_agent_path = os.path.join(self.prompt_dir, f'micro/{micro_agent_name}.md')
        if not os.path.exists(micro_agent_path):
            raise FileNotFoundError(
                f'Micro agent file {micro_agent_path} for {micro_agent_name} is not found'
            )
        with open(micro_agent_path, 'r') as file:
            return file.read()

    @property
    def system_message(self) -> str:
        rendered = self.system_template.render(
            agent_skills_docs=self.agent_skills_docs,
        ).strip()
        return rendered

    @property
    def initial_user_message(self) -> str:
        """This is the initial user message provided to the agent
        before *actual* user instructions are provided.

        It is used to provide a demonstration of how the agent
        should behave in order to solve the user's task. And it may
        optionally contain some additional context about the user's task.
        These additional context will convert the current generic agent
        into a more specialized agent that is tailored to the user's task.
        """
        rendered = self.user_template.render(micro_agent=self.micro_agent)
        return rendered.strip()
