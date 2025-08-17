from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch


def normalize_model_name(model: str) -> str:
    """Normalize a model string to a canonical, comparable name.

    Strategy:
    - Trim whitespace
    - Lowercase
    - Keep only the basename after the last '/'
      (handles prefixes like openrouter/, litellm_proxy/, anthropic/, etc.)
    """
    name = (model or '').strip().lower()
    if '/' in name:
        name = name.split('/')[-1]
    return name


def model_matches(model: str, patterns: list[str]) -> bool:
    """Return True if the normalized model matches any of the glob patterns.

    Uses fnmatch for simple glob-style matching.
    """
    name = normalize_model_name(model)
    for pat in patterns:
        if fnmatch(name, pat):
            return True
    return False


@dataclass(frozen=True)
class ModelFeatures:
    function_calling: bool
    reasoning_effort: bool
    prompt_cache: bool
    supports_stop_words: bool


# Pattern tables capturing current behavior. Keep patterns lowercase.
FUNCTION_CALLING_PATTERNS: list[str] = [
    # Anthropic families
    'claude-3-7-sonnet*',
    'claude-3.7-sonnet*',
    'claude-sonnet-3-7-latest',
    'claude-3-5-sonnet*',
    'claude-3.5-haiku*',
    'claude-3-5-haiku*',
    'claude-sonnet-4*',
    'claude-opus-4*',
    # OpenAI families
    'gpt-4o*',
    'gpt-4.1',
    'gpt-5*',
    # o-series (keep exact o1 support per existing list)
    'o1-2024-12-17',
    'o3*',
    'o4-mini*',
    # Google Gemini
    'gemini-2.5-pro*',
    # Others
    'kimi-k2-0711-preview',
    'kimi-k2-instruct',
    'qwen3-coder*',
    'qwen3-coder-480b-a35b-instruct',
]

REASONING_EFFORT_PATTERNS: list[str] = [
    'o1*',
    'o3*',
    'o4-mini*',
    'gemini-2.5-flash',
    'gemini-2.5-pro*',
    'gpt-5*',
    'claude-opus-4-1-20250805',
]

PROMPT_CACHE_PATTERNS: list[str] = [
    'claude-3-7-sonnet*',
    'claude-3.7-sonnet*',
    'claude-sonnet-3-7-latest',
    'claude-3-5-sonnet*',
    'claude-3-5-haiku*',
    'claude-3-haiku-20240307',
    'claude-3-opus-20240229',
    'claude-sonnet-4*',
    'claude-opus-4*',
]

SUPPORTS_STOP_WORDS_FALSE_PATTERNS: list[str] = [
    # o1 family doesn't support stop words
    'o1*',
    # grok-4 specific model name (basename)
    'grok-4-0709',
]


def get_features(model: str) -> ModelFeatures:
    function_calling = model_matches(model, FUNCTION_CALLING_PATTERNS)
    reasoning_effort = model_matches(model, REASONING_EFFORT_PATTERNS)
    prompt_cache = model_matches(model, PROMPT_CACHE_PATTERNS)
    supports_stop_words = not model_matches(model, SUPPORTS_STOP_WORDS_FALSE_PATTERNS)
    return ModelFeatures(
        function_calling=function_calling,
        reasoning_effort=reasoning_effort,
        prompt_cache=prompt_cache,
        supports_stop_words=supports_stop_words,
    )
