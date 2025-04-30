from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_DELEGATE_TO_CODEACT_AGENT_DESCRIPTION = """A tool that allows the agent to delegate tasks to the CodeAct agent. The CodeAct agent is capable of solving development tasks.
"""

DelegateToCodeActAgentTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='delegate_to_codeact_agent',
        description=_DELEGATE_TO_CODEACT_AGENT_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'task': {
                    'description': 'The task to delegate to the CodeAct agent. Must be in a single line.',
                    'type': 'string',
                },
            },
            'required': ['task'],
            'additionalProperties': False,
        },
    ),
)

_DELEGATE_TO_TASKSOLVING_AGENT_DESCRIPTION = """A tool that allows the agent to delegate tasks to the TaskSolving agent. The TaskSolving agent is capable of solving general tasks.
"""

DelegateToTaskSolvingAgentTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='delegate_to_tasksolving_agent',
        description=_DELEGATE_TO_TASKSOLVING_AGENT_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'task': {
                    'description': 'The task to delegate to the TaskSolving agent. Must be in a single line.',
                    'type': 'string',
                },
            },
            'required': ['task'],
            'additionalProperties': False,
        },
    ),
)
