from litellm import ChatCompletionToolParam

DelegateTool = ChatCompletionToolParam(
    type='function',
    function={
        'name': 'delegate',
        'description': 'Delegate a task to another agent.',
        'parameters': {
            'type': 'object',
            'properties': {
                'agent': {
                    'type': 'string',
                    'description': 'The name of the agent to delegate to.',
                },
                'inputs': {
                    'type': 'object',
                    'description': 'The inputs to pass to the agent.',
                },
            },
            'required': ['agent', 'inputs'],
        },
    },
)
