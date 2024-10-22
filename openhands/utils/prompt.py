from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

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
        micro_agent (MicroAgent | None): Micro-agent, if specified.
    """

    def __init__(
        self,
        prompt_dir: str,
        agent_skills_docs: str,
        micro_agent: MicroAgent | None = None,
    ):
        self.prompt_dir: str = prompt_dir
        self.agent_skills_docs: str = agent_skills_docs
        self.micro_agent: MicroAgent | None = micro_agent
        self.conversation_history: str = ''

        # initialize Jinja2 Environment with FileSystemLoader
        self.env = Environment(
            loader=FileSystemLoader(self.prompt_dir),
            autoescape=select_autoescape(['j2', 'md']),
        )

        # load templates using the environment
        self.system_template: Template = self._load_template('system_prompt')
        self.memory_template: Template = self._load_template('memory_prompt')
        self.user_template: Template = self._load_template('user_prompt')
        self.summarize_template: Template = self._load_template('summarize_prompt')

    def _load_template(self, template_name: str):
        """
        Loads a Jinja2 template using the configured environment.

        Args:
            template_name: The base name of the template file

        Returns:
            Template: The loaded Jinja2 template.
        """
        try:
            template = self.env.get_template(f'{template_name}.j2')
            print(f'Loaded template {template_name}')
            return template
        except Exception as e:
            print(f'Error loading template {template_name}: {e}')
            return Template('')

    @property
    def system_message(self) -> str:
        """
        Renders the system message template with the necessary variables.

        Returns:
            str: The rendered system message.
        """
        rendered = self.system_template.render(
            agent_skills_docs=self.agent_skills_docs,
            memory_template=self.memory_template.render(),
        ).strip()
        return rendered

    @property
    def initial_user_message(self) -> str:
        """
        Renders the initial user message template.

        Returns:
            str: The rendered initial user message.
        """
        rendered = self.user_template.render(
            micro_agent=self.micro_agent.content if self.micro_agent else None
        )
        return rendered.strip()

    @property
    def summarize_message(self) -> str:
        """
        Renders the summarize message template.

        Returns:
            str: The rendered summarize message.
        """
        rendered = self.summarize_template.render(
            conversation_history=self.conversation_history
        )
        return rendered.strip()
