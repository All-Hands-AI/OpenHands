import importlib
import os

import yaml
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

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
        micro_agent: MicroAgent | None = None,
    ) -> None:
        """
        Initializes the PromptManager with the given prompt directory and agent skills documentation.

        Args:
            prompt_dir: The directory containing the prompt templates.
            agent_skills_docs: The documentation for the agent's skills.
            micro_agent: The micro-agent to use for generating responses.
        """
        self.prompt_dir = prompt_dir
        self.micro_agent = micro_agent

        self.env = Environment(loader=FileSystemLoader(prompt_dir))

        # load available skills from YAML
        yaml_path = os.path.join(prompt_dir, 'agent.yaml')
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            self._system_template = self._load_template(
                config['template']['system_prompt']
            )
            self._agent_skills_template = self._load_template(
                config['template']['agent_skills']
            )
            self._user_template = self._load_template(config['template']['user_prompt'])
            self._examples_template = self._load_template(
                config['template']['examples']
            )

            self.available_skills = config['agent_skills']['available_skills']
        else:
            self._system_template = self._load_template('system_prompt')
            self._agent_skills_template = self._load_template('agent_skills')
            self._user_template = self._load_template('user_prompt')
            self._examples_template = self._load_template('examples')
            self.available_skills = []  # default to empty list if YAML not found

        # TODO: agent config should have a tool use enabled or disabled
        # and we can use that to conditionally load the tools variant of agentskills

    def _load_template(self, template_name: str) -> Template:
        # use the jinja2 environment to load the template
        try:
            return self.env.get_template(f'{template_name}.j2')
        except TemplateNotFound:
            # try to load from the prompt_dir
            template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
            if not os.path.exists(template_path):
                raise FileNotFoundError(f'Prompt file {template_path} not found')
            with open(template_path, 'r') as file:
                return Template(file.read())

    @property
    def system_message(self) -> str:
        # render the agent_skills.j2 template

        self.env.globals['get_skill_docstring'] = self._get_skill_docstring
        rendered_docs = self._agent_skills_template.render(
            available_skills=self.available_skills
        )

        rendered = self._system_template.render(
            agent_skills_docs=rendered_docs,
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
        # this should render the examples.j2 template first, then the user_prompt.j2 template
        rendered_examples = self._examples_template.render()
        rendered = self._user_template.render(
            examples=rendered_examples,
            micro_agent=self.micro_agent.content if self.micro_agent else None,
        )
        return rendered.strip()

    def _get_skill_docstring(self, skill_name: str) -> str:
        """Retrieves the docstring of a skill function."""
        module_name, function_name = skill_name.split(':')
        try:
            module = importlib.import_module(
                f'openhands.runtime.plugins.agent_skills.{module_name}'
            )
            function = getattr(module, function_name)
            cur_doc = function.__doc__
            # remove indentation from docstring and extra empty lines
            cur_doc = '\n'.join(
                filter(None, map(lambda x: x.strip(), cur_doc.split('\n')))
            )
            # now add a consistent 4 indentation
            cur_doc = '\n'.join(map(lambda x: ' ' * 4 + x, cur_doc.split('\n')))
            return f'{function.__name__}\n{cur_doc}'
        except (ImportError, AttributeError):
            return f'Documentation not found for skill: {skill_name}'
