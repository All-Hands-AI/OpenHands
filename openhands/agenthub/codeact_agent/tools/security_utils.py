"""Security utility constants for tool risk descriptions.

This file contains standardized risk description text for various tools.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from openhands.core.logger import openhands_logger as logger

# Set up Jinja environment with autoescape for security
TEMPLATE_DIR = Path(__file__).parent / 'security_utils_templates'
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


def _load_template(template_name: str) -> str:
    """Load and render a template from the templates directory.

    Args:
        template_name: The name of the template file without extension

    Returns:
        The rendered template as a string

    Raises:
        TemplateNotFound: If the template file doesn't exist
    """
    try:
        template = env.get_template(f'{template_name}.j2')
        return template.render()
    except TemplateNotFound as e:
        logger.error(f'Security template not found: {template_name}.j2')
        raise e


# Browser tool risk description
BROWSER_RISK_DESC = _load_template('browser')

# Bash tool risk description
BASH_RISK_DESC = _load_template('bash')

# IPython tool risk description
IPYTHON_RISK_DESC = _load_template('ipython')

# String replace editor tool risk description
STR_REPLACE_EDITOR_RISK_DESC = _load_template('str_replace_editor')

# LLM-based edit tool risk description
LLM_BASED_EDIT_RISK_DESC = _load_template('llm_based_edit')

# Risk level enum values - common across all tools
RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH']
