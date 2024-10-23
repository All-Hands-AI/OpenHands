import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from openhands.utils.microagent import MicroAgent


class PromptManager:
    """
    Manages prompt templates and micro-agents for AI interactions.

    This class handles loading and rendering of system and user prompt templates,
    as well as loading micro-agent specifications. It provides methods to access
    rendered system and initial user messages for AI interactions.
    """

    def __init__(
        self,
        prompt_dir: str | Path,
        agent_skills_docs: str,
        micro_agent: MicroAgent | None = None,
        custom_prompt_dir: str | Path | None = None,
    ):
        """Initialize PromptManager with template directories and agent configuration.

        The system supports two types of templates:
        1. Simple .md files - For basic customization with variable substitution
        2. Advanced .j2 files - For complex templates using Jinja2 features

        Templates are loaded in this order (later ones override earlier ones):
        1. Default templates from prompt_dir
        2. Custom templates from custom_prompt_dir
        3. .j2 files take precedence over .md files with the same base name
        """
        self.prompt_dir = os.path.abspath(prompt_dir)
        self.agent_skills_docs = agent_skills_docs
        self.micro_agent = micro_agent
        self.conversation_history: list[dict[str, Any]] = []
        self.core_memory: str = ''

        # Set up template search paths with custom templates taking precedence
        template_dirs = [self.prompt_dir]
        if custom_prompt_dir:
            template_dirs.insert(0, os.path.abspath(custom_prompt_dir))

        # Initialize Jinja environment
        self.env = Environment(
            loader=FileSystemLoader(template_dirs),
            autoescape=select_autoescape(['j2', 'md']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Load all templates
        self.templates = self._load_templates()

    def _load_templates(self) -> dict[str, Template]:
        """Load templates with appropriate extensions based on complexity.

        For each template name (e.g. 'system_prompt'), checks for files in this order:
        1. {name}.j2 in custom_prompt_dir (if provided)
        2. {name}.md in custom_prompt_dir (if provided)
        3. {name}.j2 in prompt_dir
        4. {name}.md in prompt_dir
        """
        templates = {}

        # Template names and their default types
        template_configs = {
            # Complex templates that typically need Jinja features
            'system_prompt': '.j2',
            'summarize_prompt': '.j2',
            # Simple templates that work well as markdown
            'user_prompt': '.md',
            'examples': '.md',
        }

        for name, default_ext in template_configs.items():
            # Try loading template with either extension
            template = None
            for ext in ['.j2', '.md']:
                try:
                    template = self.env.get_template(f'{name}{ext}')
                    break
                except Exception:
                    continue

            # If no template found, create empty one with default extension
            if template is None:
                print(f'No template found for {name}, using empty template')
                template = self.env.from_string('')

            templates[name] = template

        return templates

    def get_template_variables(self) -> dict[str, Any]:
        """Get the current template variables.

        Returns:
            Dictionary of variables available to templates
        """
        return {
            'agent_skills_docs': self.agent_skills_docs,
            'core_memory': self.core_memory,
            'conversation_history': self.conversation_history,
            'micro_agent': self.micro_agent.content if self.micro_agent else None,
        }

    @property
    def system_message(self) -> str:
        """Render the system message template."""
        return (
            self.templates['system_prompt']
            .render(**self.get_template_variables())
            .strip()
        )

    @property
    def initial_user_message(self) -> str:
        """Render the initial user message template."""
        return (
            self.templates['user_prompt']
            .render(**self.get_template_variables())
            .strip()
        )

    @property
    def summarize_message(self) -> str:
        """Render the summarize message template."""
        return (
            self.templates['summarize_prompt']
            .render(**self.get_template_variables())
            .strip()
        )
