"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json
from litellm import (
    ChatCompletionToolParam,
    ModelResponse,
)

from openhands.agenthub.loc_agent.tools import (
    FinishTool,
    SearchEntityTool, 
    SearchRepoTool,
    ExploreTreeStructureTool,
    ExploreTreeStructureTool_simple
)
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
    FunctionCallValidationError,
)
from openhands.events.action import (
    Action,
    # AgentDelegateAction,
    AgentFinishAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.tool import ToolCallMetadata

ALL_FUNCTIONS = ['explore_tree_structure', 'search_code_snippets', 'get_entity_contents']

def combine_thought(action: Action, thought: str) -> Action:
    if not hasattr(action, 'thought'):
        return action
    if thought and action.thought:
        action.thought = f'{thought}\n{action.thought}'
    elif thought:
        action.thought = thought
    return action


def response_to_actions(response: ModelResponse) -> list[Action]:
    actions: list[Action] = []
    assert len(response.choices) == 1, 'Only one choice is supported for now'
    choice = response.choices[0]
    assistant_msg = choice.message
    if hasattr(assistant_msg, 'tool_calls') and assistant_msg.tool_calls:
        # Check if there's assistant_msg.content. If so, add it to the thought
        thought = ''
        if isinstance(assistant_msg.content, str):
            thought = assistant_msg.content
        elif isinstance(assistant_msg.content, list):
            for msg in assistant_msg.content:
                if msg['type'] == 'text':
                    thought += msg['text']

        # Process each tool call to OpenHands action
        for i, tool_call in enumerate(assistant_msg.tool_calls):
            action: Action
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.decoder.JSONDecodeError as e:
                raise RuntimeError(
                    f'Failed to parse tool call arguments: {tool_call.function.arguments}'
                ) from e

            # ================================================
            # IPythonTool (Jupyter)
            # ================================================
            if tool_call.function.name in ALL_FUNCTIONS:
                # We implement this in agent_skills, which can be used via Jupyter
                func_name = tool_call.function.name
                code = f'print({func_name}(**{arguments}))'
                logger.debug(f'TOOL CALL: {func_name} with code: {code}')
                action = IPythonRunCellAction(code=code)

            # ================================================
            # AgentFinishAction
            # ================================================
            elif tool_call.function.name == FinishTool['function']['name']:
                action = AgentFinishAction(
                    final_thought=arguments.get('message', ''),
                    task_completed=arguments.get('task_completed', None),
                )
            else:
                raise FunctionCallNotExistsError(
                    f'Tool {tool_call.function.name} is not registered. (arguments: {arguments}). Please check the tool name and retry with an existing tool.'
                )
            # We only add thought to the first action
            if i == 0:
                action = combine_thought(action, thought)
            # Add metadata for tool calling
            action.tool_call_metadata = ToolCallMetadata(
                tool_call_id=tool_call.id,
                function_name=tool_call.function.name,
                model_response=response,
                total_calls_in_response=len(assistant_msg.tool_calls),
            )
            actions.append(action)
    else:
        actions.append(
            MessageAction(
                content=str(assistant_msg.content) if assistant_msg.content else '',
                wait_for_response=True,
            )
        )

    assert len(actions) >= 1
    return actions


def get_tools(
        enable_search_keyword: bool = False,
        enable_search_entity: bool = False,
        enable_tree_structure_traverser: bool = False,
        simple_desc: bool = False,
) -> list[ChatCompletionToolParam]:
    tools = [FinishTool]
    # if codeact_enable_cmd:
    #     tools.append(CmdRunTool)
    if enable_search_keyword:
        tools.append(SearchRepoTool)
    if enable_search_entity:
        tools.append(SearchEntityTool)
    if enable_tree_structure_traverser:
        if simple_desc:
            tools.append(ExploreTreeStructureTool_simple)
        else:
            tools.append(ExploreTreeStructureTool)
    return tools