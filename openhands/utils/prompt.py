import importlib
import os
from inspect import signature

import yaml
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from openhands.core.logger import openhands_logger as logger
from openhands.utils.microagent import MicroAgent


class PromptManager:
    """
    Manages prompt templates and micro-agents for AI interactions.

    This class handles loading and rendering of system and user prompt templates,
    as well as loading micro-agent specifications. It provides methods to access
    rendered system and initial user messages for AI interactions.

    Attributes:
        prompt_dir (str): Directory containing prompt templates.
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
            micro_agent: The micro-agent to use for generating responses.
        """
        self.prompt_dir = prompt_dir
        self.micro_agent = micro_agent

        # load configuration from agent.yaml
        yaml_path = os.path.join(prompt_dir, 'agent.yaml')
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                self.config = yaml.safe_load(f)

            custom_templates_dir = self.config.get('custom_templates_dir', None)
            if custom_templates_dir:
                custom_templates_dir = os.path.abspath(custom_templates_dir)

                # prioritize custom_templates_dir over the default templates directory
                self.env = Environment(
                    loader=FileSystemLoader([custom_templates_dir, self.prompt_dir])
                )
            else:
                self.env = Environment(loader=FileSystemLoader(self.prompt_dir))

            # load templates and blocks
            template_config = self.config['template']
            self.templates = {}
            for name, cfg in template_config.items():
                template = self._load_template(cfg['file'])
                self.templates[name] = {
                    'template': template,
                    'blocks': cfg.get('blocks', []),
                }

            self.available_skills = self.config['agent_skills']['available_skills']
        else:
            # load default templates if agent.yaml is not present
            self.env = Environment(loader=FileSystemLoader(self.prompt_dir))
            self.templates = self._load_default_templates()
            self.available_skills = []

        # TODO: agent config will have tool use enabled or disabled
        # to conditionally load the tools variant of agentskills

    def _load_template(self, template_name: str) -> Template:
        """Loads a Jinja2 template by name."""
        try:
            return self.env.get_template(f'{template_name}.j2')
        except TemplateNotFound:
            # try to load from the prompt_dir
            template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
            if not os.path.exists(template_path):
                raise FileNotFoundError(f'Prompt file {template_path} not found')
            with open(template_path, 'r') as file:
                return Template(file.read())

    def _load_default_templates(self) -> dict:
        """Loads default template configuration when no agent.yaml is present.

        Returns:
            Dictionary with default templates.
        """
        # load all default templates
        templates = {}

        # system prompt with standard block order
        templates['system_prompt'] = {
            'template': self._load_template('system_prompt'),
            'blocks': [
                'system_prefix',
                'python_capabilities',
                'bash_capabilities',
                'browsing_capabilities',
                'pip_capabilities',
                'agent_skills',
                'system_rules',
            ],
        }

        # agent skills documentation
        templates['agent_skills'] = {
            'template': self._load_template('agent_skills'),
            'blocks': ['skill_docs'],
        }

        # example interactions
        templates['examples'] = {
            'template': self._load_template('examples'),
        }

        # micro-agent guidelines
        templates['micro_agent'] = {
            'template': self._load_template('micro_agent'),
            'blocks': ['micro_agent_guidelines'],
        }

        # user prompt combining everything
        templates['user_prompt'] = {
            'template': self._load_template('user_prompt'),
            'blocks': ['user_prompt', 'default_example', 'micro_agent_guidelines'],
        }

        return templates

    def _render_blocks(self, template_name: str, **kwargs) -> str:
        """Renders template blocks in the specified order with shared context.

        Args:
            template_name: Name of the template to render.
            **kwargs: Variables to pass to the template context.

        Returns:
            Rendered string combining all blocks in order.
        """
        template_info = self.templates.get(template_name)
        if not template_info:
            logger.error(f"Template '{template_name}' not found.")
            return ''

        rendered_blocks = []

        # create a new template context that will be shared across all blocks
        context = template_info['template'].new_context(kwargs)

        # render each block using the shared context
        for block_name in template_info.get('blocks', []):
            try:
                logger.debug(f"Rendering block '{template_name}.{block_name}'")
                block = template_info['template'].blocks[block_name]
                rendered = ''.join(block(context))
                rendered_blocks.append(rendered)
            except KeyError:
                logger.warning(
                    f"Block '{block_name}' not found in template '{template_name}'"
                )
                continue

        return ''.join(rendered_blocks)

    @property
    def system_message(self) -> str:
        """Renders and returns the system message."""
        self.env.globals['get_skill_docstring'] = self._get_skill_docstring

        # render agent skills blocks first
        rendered_docs = self._render_blocks(
            'agent_skills', available_skills=self.available_skills
        ).strip()

        # then render system blocks with agent skills included
        rendered = self._render_blocks('system_prompt', agent_skills_docs=rendered_docs)
        return rendered.strip()

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
        # render each component's blocks
        rendered_examples = self._render_blocks('examples').strip()
        rendered_micro_agent = self._render_blocks(
            'micro_agent',
            micro_agent=self.micro_agent.content if self.micro_agent else None,
        ).strip()

        # combine in user prompt
        rendered = self._render_blocks(
            'user_prompt',
            examples=rendered_examples,
            micro_agent_content=rendered_micro_agent,
        )
        return rendered.strip()

    def _get_skill_docstring(self, skill_name: str) -> str:
        """Retrieves the docstring of a skill function."""
        module_name, function_name = skill_name.split(':')
        try:
            module = importlib.import_module(
                f'openhands.runtime.plugins.agent_skills.{module_name}'
            )

            # find the function
            agent_skill_fn = getattr(module, function_name)

            # get the function signature with parameter names, types and return type
            fn_signature = f'{agent_skill_fn.__name__}' + str(signature(agent_skill_fn))

            doc = agent_skill_fn.__doc__

            # remove indentation from docstring and extra empty lines
            doc = '\n'.join(filter(None, map(lambda x: x.strip(), doc.split('\n'))))

            # now add a consistent 4 indentation
            doc = '\n'.join(map(lambda x: ' ' * 4 + x, doc.split('\n')))
            return f'{fn_signature}\n{doc}'
        except (ImportError, AttributeError) as e:
            logger.error(e)
            return f'Documentation not found for skill: {skill_name}'
