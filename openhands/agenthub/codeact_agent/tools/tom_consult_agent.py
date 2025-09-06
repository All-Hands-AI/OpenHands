"""Tom consult agent tool definition for CodeAct agent."""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_CONSULT_TOM_AGENT_DESCRIPTION = """Consult Tom agent for guidance when you need help understanding user intent or task requirements.

This tool allows you to consult Tom agent for personalized guidance based on user modeling. Use this when:
- User instructions are vague or unclear
- You need help understanding what the user actually wants
- You want guidance on the best approach for the current task
- You have your own question for Tom agent about the task or user's needs

By default, Tom agent will analyze the user's message. Optionally, you can ask a custom question."""

ConsultTomAgentTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='consult_tom_agent',
        description=_CONSULT_TOM_AGENT_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'reason': {
                    'type': 'string',
                    'description': 'Brief explanation of why you need Tom agent consultation',
                },
                'use_user_message': {
                    'type': 'boolean',
                    'description': 'Whether to consult about the user message (true) or provide custom query (false)',
                    'default': True,
                },
                'custom_query': {
                    'type': 'string',
                    'description': 'Custom query to ask Tom agent (only used when use_user_message is false)',
                },
            },
            'required': ['reason'],
        },
    ),
)
