"""Task planning tool for the Automation Agent."""

from typing import Any, Optional

from litellm import ChatCompletionToolParam

TaskPlannerTool: ChatCompletionToolParam = {
    'type': 'function',
    'function': {
        'name': 'plan_task',
        'description': """
        Break down complex tasks into manageable subtasks and create execution plans.

        This tool can:
        - Analyze complex requirements
        - Break down tasks into subtasks
        - Identify dependencies between tasks
        - Estimate time and resources needed
        - Create execution timelines
        - Prioritize tasks
        - Identify potential risks and mitigation strategies
        - Generate project plans

        Use this tool when you need to plan and organize complex multi-step tasks.
        """,
        'parameters': {
            'type': 'object',
            'properties': {
                'main_task': {
                    'type': 'string',
                    'description': 'The main task or objective to plan',
                },
                'complexity': {
                    'type': 'string',
                    'enum': ['low', 'medium', 'high', 'very_high'],
                    'description': 'Complexity level of the task',
                },
                'deadline': {
                    'type': 'string',
                    'description': 'Deadline for task completion (optional)',
                },
                'resources': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Available resources and tools',
                },
                'constraints': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Constraints or limitations to consider',
                },
                'success_criteria': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Criteria for successful completion',
                },
                'planning_depth': {
                    'type': 'string',
                    'enum': ['high_level', 'detailed', 'comprehensive'],
                    'description': 'Level of detail for the plan',
                },
            },
            'required': ['main_task'],
        },
    },
}


def execute_task_planning(
    main_task: str,
    complexity: str = 'medium',
    deadline: Optional[str] = None,
    resources: Optional[list[str]] = None,
    constraints: Optional[list[str]] = None,
    success_criteria: Optional[list[str]] = None,
    planning_depth: str = 'detailed',
) -> dict[str, Any]:
    """
    Execute task planning.

    Args:
        main_task: The main task to plan
        complexity: Complexity level
        deadline: Deadline for completion
        resources: Available resources
        constraints: Constraints to consider
        success_criteria: Success criteria
        planning_depth: Level of planning detail

    Returns:
        Dictionary containing the task plan
    """
    # This would be implemented to actually create task plans
    # For now, return a placeholder structure
    return {
        'main_task': main_task,
        'complexity': complexity,
        'deadline': deadline,
        'subtasks': [
            {
                'id': 'subtask_1',
                'description': f'Analyze requirements for {main_task}',
                'priority': 1,
                'estimated_time': '2 hours',
                'dependencies': [],
                'resources_needed': ['research_tool'],
            },
            {
                'id': 'subtask_2',
                'description': f'Execute main components of {main_task}',
                'priority': 2,
                'estimated_time': '4 hours',
                'dependencies': ['subtask_1'],
                'resources_needed': ['development_tools'],
            },
            {
                'id': 'subtask_3',
                'description': f'Verify and finalize {main_task}',
                'priority': 3,
                'estimated_time': '1 hour',
                'dependencies': ['subtask_2'],
                'resources_needed': ['verification_tool'],
            },
        ],
        'total_estimated_time': '7 hours',
        'critical_path': ['subtask_1', 'subtask_2', 'subtask_3'],
        'risks': [
            {
                'risk': 'Resource availability',
                'probability': 'medium',
                'impact': 'medium',
                'mitigation': 'Prepare alternative resources',
            }
        ],
        'success_criteria': success_criteria or [f'Successfully complete {main_task}'],
        'planning_depth': planning_depth,
        'created_at': '2024-01-01T00:00:00Z',
    }
