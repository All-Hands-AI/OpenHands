"""Tom improve instruction tool definition for CodeAct agent."""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_IMPROVE_INSTRUCTION_DESCRIPTION = """Improve user instructions using the Tom agent when current user instructions need enhancement or clarification.

This tool analyzes the current user instruction and conversation context to suggest improvements that could lead to better task completion. Use this when:
- User instructions are vague or unclear
- Instructions lack important technical details
- You believe enhanced instructions would improve task success
- The current instruction could benefit from Tom's user modeling expertise

The tool will initiate a collaborative instruction improvement process by communicating with the Tom agent."""

ImproveInstructionTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='improve_instruction',
        description=_IMPROVE_INSTRUCTION_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'reason': {
                    'type': 'string',
                    'description': 'Brief explanation of why you think this instruction should be improved',
                }
            },
            'required': ['reason'],
        },
    ),
)
