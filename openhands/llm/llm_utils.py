import copy
from typing import TYPE_CHECKING, Any

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.model_features import get_features

if TYPE_CHECKING:
    from litellm import ChatCompletionToolParam


def check_tools(
    tools: list['ChatCompletionToolParam'], llm_config: LLMConfig
) -> list['ChatCompletionToolParam']:
    """Checks and modifies tools for compatibility with the current LLM."""
    # Special handling for Gemini models which don't support default fields and have limited format support
    if 'gemini' in llm_config.model.lower():
        logger.info(
            f'Removing default fields and unsupported formats from tools for Gemini model {llm_config.model} '
            "since Gemini models have limited format support (only 'enum' and 'date-time' for STRING types)."
        )
        # prevent mutation of input tools
        checked_tools = copy.deepcopy(tools)
        # Strip off default fields and unsupported formats that cause errors with gemini-preview
        for tool in checked_tools:
            if 'function' in tool and 'parameters' in tool['function']:
                if 'properties' in tool['function']['parameters']:
                    for prop_name, prop in tool['function']['parameters'][
                        'properties'
                    ].items():
                        # Remove default fields
                        if 'default' in prop:
                            del prop['default']

                        # Remove format fields for STRING type parameters if the format is unsupported
                        # Gemini only supports 'enum' and 'date-time' formats for STRING type
                        if prop.get('type') == 'string' and 'format' in prop:
                            supported_formats = ['enum', 'date-time']
                            if prop['format'] not in supported_formats:
                                logger.info(
                                    f'Removing unsupported format "{prop["format"]}" for STRING parameter "{prop_name}"'
                                )
                                del prop['format']
        return checked_tools
    return tools


def prepare_reasoning_model_kwargs(
    kwargs: dict[str, Any], model: str, reasoning_effort: str | None
) -> None:
    """Prepare kwargs for reasoning models.

    Handles reasoning_effort parameter and removes incompatible parameters
    like temperature and top_p.

    This function modifies kwargs in-place to ensure compatibility with reasoning
    models (Claude Sonnet-4-5, o3, Gemini-2.5-pro, etc.) which don't support
    temperature/top_p when using reasoning capabilities.

    Args:
        kwargs: Dictionary of parameters to be passed to the LLM API (modified in-place)
        model: The model identifier string
        reasoning_effort: The reasoning effort level from config

    Note:
        - For Gemini-2.5-pro: Maps 'low'/'none'/None to thinking budget tokens
        - For Claude Sonnet-4-5: Removes reasoning_effort parameter
        - For other reasoning models: Sets reasoning_effort parameter
        - Always removes temperature and top_p for reasoning models
    """
    features = get_features(model)
    if not features.supports_reasoning_effort:
        return

    # Handle model-specific reasoning effort parameter
    if 'gemini-2.5-pro' in model:
        logger.debug(f'Gemini model {model} with reasoning_effort {reasoning_effort}')
        if reasoning_effort in {None, 'low', 'none'}:
            kwargs['thinking'] = {'budget_tokens': 128}
            kwargs['allowed_openai_params'] = ['thinking']
            kwargs.pop('reasoning_effort', None)
        else:
            kwargs['reasoning_effort'] = reasoning_effort
        logger.debug(
            f'Gemini model {model} with reasoning_effort {reasoning_effort} '
            f'mapped to thinking {kwargs.get("thinking")}'
        )
    elif 'claude-sonnet-4-5' in model:
        # Claude Sonnet 4.5 doesn't accept reasoning_effort parameter
        kwargs.pop('reasoning_effort', None)
    else:
        kwargs['reasoning_effort'] = reasoning_effort

    # Remove incompatible parameters for all reasoning models
    kwargs.pop('temperature', None)
    kwargs.pop('top_p', None)
