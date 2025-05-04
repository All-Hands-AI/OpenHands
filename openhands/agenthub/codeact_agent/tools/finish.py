from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_FINISH_DESCRIPTION = """Signals the completion of the current task or conversation.

Use this tool when:
- You have successfully completed the user's requested task
- You cannot proceed further due to technical limitations or missing information

The outputs should include:
- A dictionary of task results and outputs
- Any data or information produced by the task

The thought should describe:
- What actions were taken
- Why those actions were chosen
- Any key decisions made

The final_thought should include:
- A clear summary of actions taken and their results
- Any next steps for the user
- Explanation if you're unable to complete the task
- Any follow-up questions if more information is needed

The task_completed field should be set to True if you believed you have completed the task, and False otherwise.
"""

FinishTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='finish',
        description=_FINISH_DESCRIPTION,
        parameters={
            'type': 'object',
            'required': ['outputs', 'thought', 'task_completed', 'final_thought'],
            'properties': {
                'outputs': {
                    'type': 'object',
                    'description': 'Dictionary containing the results and outputs of the task',
                },
                'thought': {
                    'type': 'string',
                    'description': 'Description of what actions were taken and why',
                },
                'task_completed': {
                    'type': 'string',
                    'enum': ['true', 'false', 'partial'],
                    'description': 'Whether you have completed the task.',
                },
                'final_thought': {
                    'type': 'string',
                    'description': 'Final summary of the task, including results and next steps',
                },
            },
        },
    ),
)
