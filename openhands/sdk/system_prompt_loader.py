from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def load_codeact_system_prompt(render: bool = True) -> str:
    """Load and render the CodeActAgent system prompt copied under SDK prompts.

    Renders includes with cli_mode=True to match CLIRuntime semantics.
    """
    prompts_dir = Path(__file__).resolve().parent / 'prompts'
    system_prompt_path = prompts_dir / 'system_prompt.j2'
    if not system_prompt_path.exists():
        return 'You are OpenHands agent, a helpful AI assistant that can interact with a computer to solve tasks.'
    if not render:
        return system_prompt_path.read_text(encoding='utf-8')
    env = Environment(loader=FileSystemLoader(str(prompts_dir)))
    tpl = env.get_template('system_prompt.j2')
    rendered = tpl.render(cli_mode=True).strip()
    try:
        from openhands.agenthub.codeact_agent.tools.prompt import refine_prompt

        rendered = refine_prompt(rendered)
    except Exception:
        pass
    return rendered
