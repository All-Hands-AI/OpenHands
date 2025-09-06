from pathlib import Path

import jinja2


def load_prompt(prompt: str, **kwargs) -> str:
    """Load a prompt by name. Passes all the keyword arguments to the prompt template."""
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(Path(__file__).parent))
    template = env.get_template(f'{prompt}.j2')
    return template.render(**kwargs)


__all__ = ['load_prompt']
