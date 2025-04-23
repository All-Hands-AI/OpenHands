import json

from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)

from openhands.core.exceptions import (
    FunctionCallNotExistsError,
    FunctionCallValidationError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.tool import ToolCallMetadata

_DELEGATE_LOCAL = """Delegate a task to a local agent hosted on a same instance.
"""

DelegateLocalTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='delegate_local',
        description=_DELEGATE_LOCAL,
        parameters={
            'type': 'object',
            'properties': {
                'agent_name': {
                    'type': 'string',
                    'description': 'The name of the agent to delegate to.',
                },
                'task': {
                    'type': 'string',
                    'description': 'The task to delegate.',
                },
            },
            'required': ['agent_name', 'task'],
        },
    ),
)

_DELEGATE_REMOTE = """Delegate a task to a remote agent hosted on a remote server using A2A Protocol.
"""

DelegateRemoteTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='delegate_remote',
        description=_DELEGATE_REMOTE,
        parameters={
            'type': 'object',
            'properties': {
                'url': {
                    'type': 'string',
                    'description': 'The URL of the remote agent.',
                },
                'task': {
                    'type': 'string',
                    'description': 'The task to delegate.',
                },
                'session_id': {
                    'type': 'string',
                    'description': 'The session id of the remote agent.',
                },
                'task_id': {
                    'type': 'string',
                    'description': 'The task id of the remote agent.',
                }
            },
            'required': ['url', 'task'],
        },
    ),
)

_FINISH_DESCRIPTION = """Finish the interaction when the task is complete OR if the assistant cannot proceed further with the task."""

FinishTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='finish',
        description=_FINISH_DESCRIPTION,
    ),
)


def combine_thought(action: Action, thought: str) -> Action:
    if not hasattr(action, 'thought'):
        return action
    if thought:
        action.thought = thought
    return action


def response_to_action(response: ModelResponse) -> Action:
    action: Action = None  # type: ignore
    assert len(response.choices) == 1, 'Only one choice is supported for now'
    assistant_msg = response.choices[0].message
    if assistant_msg.tool_calls:
        # Check if there's assistant_msg.content. If so, add it to the thought
        thought = ''
        if isinstance(assistant_msg.content, str):
            thought = assistant_msg.content
        elif isinstance(assistant_msg.content, list):
            for msg in assistant_msg.content:
                if msg['type'] == 'text':
                    thought += msg['text']

        # Assume only one tool call is returned
        if len(assistant_msg.tool_calls) != 1:
            logger.info(
                f'Expected only one tool call, but got {len(assistant_msg.tool_calls)}'
            )
        tool_call = assistant_msg.tool_calls[0]
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.decoder.JSONDecodeError as e:
            raise RuntimeError(
                f'Failed to parse tool call arguments: {tool_call.function.arguments}'
            ) from e

        if tool_call.function.name == 'delegate_remote':
            for k in ['url', 'task']:
                if k not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "{k}" in tool call {tool_call.function.name}'
                    )
            
            message = arguments['task']
            message = message.replace('\n', '\\\n')
            url = arguments['url']
            session_id = arguments.get('session_id')
            task_id = arguments.get('task_id')
            if session_id and task_id:
                code = (
                    f'await send_task_A2A('
                    f'message="{message}", '
                    f'url="{url}", '
                    f'session_id="{session_id}", '
                    f'task_id="{task_id}")'
                )
            else:
                code = (
                    f'await send_task_A2A('
                    f'message="{message}", '
                    f'url="{url}")'
                )

            action = IPythonRunCellAction(code=code, include_extra=False)
        
        elif tool_call.function.name == 'finish':
            action = AgentFinishAction()
        else:
            raise FunctionCallNotExistsError(
                f'Tool {tool_call.function.name} is not registered. (arguments: {arguments}). Please check the tool name and retry with an existing tool.'
            )

        action = combine_thought(action, thought)
        # Add metadata for tool calling
        action.tool_call_metadata = ToolCallMetadata(
            tool_call_id=tool_call.id,
            function_name=tool_call.function.name,
            model_response=response,
            total_calls_in_response=len(assistant_msg.tool_calls),
        )

    else:
        action = MessageAction(content=assistant_msg.content, wait_for_response=True)

    return action


def get_tools() -> list[ChatCompletionToolParam]:
    tools = [DelegateLocalTool, DelegateRemoteTool, FinishTool]
    return tools
