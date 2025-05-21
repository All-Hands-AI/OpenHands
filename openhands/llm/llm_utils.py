import copy
from typing import TYPE_CHECKING

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger

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
