import copy
from typing import TYPE_CHECKING

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger

if TYPE_CHECKING:
    from litellm import ChatCompletionToolParam

# Track whether we've already logged the Gemini tool modification message
_gemini_tool_modification_logged = set()


def check_tools(
    tools: list['ChatCompletionToolParam'], llm_config: LLMConfig
) -> list['ChatCompletionToolParam']:
    """Checks and modifies tools for compatibility with the current LLM."""
    # Special handling for Gemini models which don't support default fields and have limited format support
    if 'gemini' in llm_config.model.lower():
        # Only log the main message once per model to reduce noise
        if llm_config.model not in _gemini_tool_modification_logged:
            logger.debug(
                f'Removing default fields and unsupported formats from tools for Gemini model {llm_config.model} '
                "since Gemini models have limited format support (only 'enum' and 'date-time' for STRING types)."
            )
            _gemini_tool_modification_logged.add(llm_config.model)

        # prevent mutation of input tools
        checked_tools = copy.deepcopy(tools)

        # Track if we actually modify anything to provide useful feedback
        defaults_removed = 0
        formats_removed = 0

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
                            defaults_removed += 1

                        # Remove format fields for STRING type parameters if the format is unsupported
                        # Gemini only supports 'enum' and 'date-time' formats for STRING type
                        if prop.get('type') == 'string' and 'format' in prop:
                            supported_formats = ['enum', 'date-time']
                            if prop['format'] not in supported_formats:
                                logger.debug(
                                    f'Removing unsupported format "{prop["format"]}" for STRING parameter "{prop_name}" '
                                    f'in tool "{tool.get("function", {}).get("name", "unknown")}"'
                                )
                                del prop['format']
                                formats_removed += 1

        # Log a summary if we actually modified anything, but only at debug level to reduce noise
        if defaults_removed > 0 or formats_removed > 0:
            logger.debug(
                f'Modified {len(checked_tools)} tools for Gemini compatibility: '
                f'removed {defaults_removed} default fields and {formats_removed} unsupported formats'
            )

        return checked_tools
    return tools
