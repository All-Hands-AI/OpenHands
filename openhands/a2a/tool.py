from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

ListRemoteAgents = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='a2a_list_remote_agents',
        description="""List the available remote agents you can use to delegate the task.""",
        parameters={'type': 'object', 'properties': {}, 'required': []},
    ),
)

SendTask = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='a2a_send_task',
        description="""
            Send a task to a remote agent and yield task responses.
        """,
        parameters={
            'type': 'object',
            'properties': {
                'agent_name': {
                    'type': 'string',
                    'description': 'The name of the remote agent to send the task to.',
                },
                'task_message': {
                    'type': 'string',
                    'description': 'The message to send to the remote agent.',
                },
            },
            'required': ['agent_name', 'task_message'],
        },
    ),
)
