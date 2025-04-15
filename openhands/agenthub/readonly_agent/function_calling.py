"""This file contains the function calling implementation for the ReadOnlyAgent.

It imports and reuses functionality from the CodeActAgent's function_calling module.
"""

import json
import shlex

from litellm import (
    ChatCompletionToolParam,
    ModelResponse,
)

from openhands.agenthub.codeact_agent.function_calling import (
    Action,
    BrowserAction,
    FinishAction,
    GlobAction,
    GrepAction,
    IPythonAction,
    LLMBasedFileEditAction,
    StrReplaceEditorAction,
    ThinkAction,
    ViewAction,
    WebReadAction,
    build_glob_command,
    response_to_actions,
)
from openhands.agenthub.readonly_agent.tools import (
    READ_ONLY_TOOLS,
    FinishTool,
    GlobTool,
    GrepTool,
    ThinkTool,
    ViewTool,
    WebReadTool,
)
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM


def get_tools(
    enable_browsing: bool = True,
    enable_llm_editor: bool = False,
    enable_jupyter: bool = False,
    llm: LLM | None = None,
) -> list[ChatCompletionToolParam]:
    """Get the tools for the ReadOnlyAgent.
    
    This function returns only the read-only tools, regardless of the parameters.
    
    Parameters:
    - enable_browsing: Whether to enable browsing tools (web_read)
    - enable_llm_editor: Not used in ReadOnlyAgent
    - enable_jupyter: Not used in ReadOnlyAgent
    - llm: The LLM to use
    
    Returns:
    - A list of tools that the ReadOnlyAgent can use
    """
    # ReadOnlyAgent only uses read-only tools
    tools = [
        ThinkTool,
        ViewTool,
        GrepTool,
        GlobTool,
        FinishTool,
    ]
    
    if enable_browsing:
        tools.append(WebReadTool)
    
    return tools