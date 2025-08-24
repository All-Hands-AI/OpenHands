from __future__ import annotations

from pathlib import Path


def load_codeact_system_prompt(render: bool = True) -> str:
    """Load the CodeActAgent system prompt.

    By default, returns the fully rendered template (resolves includes)
    by simply returning the main prompt content without the surrounding
    Jinja include wrapper files (the base file already inlines policy text).

    We do not evaluate Jinja variables here; the referenced system_prompt.j2
    is mostly static text with includes. Since openhands/agenthub/.../system_prompt.j2
    already contains literal content for our needs, we can return it as-is.
    If in the future variables are used, consider minimal Jinja2 rendering.
    """
    # Use repo path relative to package root
    base = (
        Path(__file__).resolve().parents[2] / 'agenthub' / 'codeact_agent' / 'prompts'
    )
    system_prompt_path = base / 'system_prompt.j2'
    if not system_prompt_path.exists():
        # fallback: return a minimal prompt
        return 'You are OpenHands agent, a helpful AI assistant that can interact with a computer to solve tasks.'
    text = system_prompt_path.read_text(encoding='utf-8')
    # The includes are already expanded in system_prompt.j2 content; we return as-is.
    return text
