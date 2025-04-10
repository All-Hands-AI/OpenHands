from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_PLANNING_DESCRIPTION = """
A planning tool that allows the agent to create and manage plans for solving complex tasks.
The tool provides functionality for creating plans, updating plan tasks, and tracking progress.
"""

PlanningTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='planning',
        description=_PLANNING_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'command': {
                    'description': 'The command to execute. Available commands: create',
                    'enum': [
                        'create',
                    ],
                    'type': 'string',
                },
                'plan_id': {
                    'description': 'Unique identifier for the plan. Required for create command.',
                    'type': 'string',
                },
                'title': {
                    'description': 'Title for the plan. Required for create command.',
                    'type': 'string',
                },
                'tasks': {
                    'description': 'List of plan tasks. Required for create command.',
                    'type': 'array',
                    'items': {'type': 'string'},
                },
            },
            'required': ['command'],
            'additionalProperties': False,
        },
    ),
)


implement_later_params = {
    'type': 'object',
    'properties': {
        'command': {
            'description': 'The command to execute. Available commands: create, update, list, get, set_active, mark_step, delete.',
            'enum': [
                'create',
                'update',
                'list',
                'get',
                'set_active',
                'mark_step',
                'delete',
            ],
            'type': 'string',
        },
        'plan_id': {
            'description': 'Unique identifier for the plan. Required for create, update, set_active, and delete commands. Optional for get and mark_step (uses active plan if not specified).',
            'type': 'string',
        },
        'title': {
            'description': 'Title for the plan. Required for create command, optional for update command.',
            'type': 'string',
        },
        'tasks': {
            'description': 'List of plan tasks. Required for create command, optional for update command.',
            'type': 'array',
            'items': {'type': 'string'},
        },
        'step_index': {
            'description': 'Index of the step to update (0-based). Required for mark_step command.',
            'type': 'integer',
        },
        'step_status': {
            'description': 'Status to set for a step. Used with mark_step command.',
            'enum': ['not_started', 'in_progress', 'completed', 'blocked'],
            'type': 'string',
        },
        'step_notes': {
            'description': 'Additional notes for a step. Optional for mark_step command.',
            'type': 'string',
        },
    },
    'required': ['command'],
    'additionalProperties': False,
}
