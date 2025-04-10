from dataclasses import asdict, dataclass, field

from openhands.events.action import Action
from openhands.events.action.plan import CreatePlanAction, MarkTaskAction, TaskStatus


@dataclass
class Task:
    """A task in a plan."""

    content: str
    status: str = TaskStatus.NOT_STARTED
    result: str = ''


@dataclass
class Plan:
    """A plan."""

    plan_id: str
    title: str
    tasks: list[Task] = field(default_factory=list)

    @classmethod
    def from_create_plan_action(cls, action: Action) -> 'Plan':
        if not isinstance(action, CreatePlanAction):
            raise ValueError(
                f'Action must be of type CreatePlanAction, not {type(action)}'
            )

        return cls(
            action.plan_id,
            action.title,
            [Task(content=content) for content in action.tasks],
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def execute_plan_action(self, action: Action) -> str:
        if isinstance(action, CreatePlanAction):
            return 'Plan already exists'
        elif isinstance(action, MarkTaskAction):
            self.tasks[action.task_index].status = action.task_status
            self.tasks[action.task_index].result = action.task_result
            return f'Task {action.task_index} masked with status {action.task_status} and result {action.task_result}'
        else:
            raise ValueError(
                f'Action must be of type CreatePlanAction or MarkTaskAction, not {type(action)}'
            )

    def _format_plan(self, w_result: bool = True) -> str:
        """Format a plan for display."""
        output = f'Plan: {self.title} (ID: {self.plan_id})\n'
        output += '=' * len(output) + '\n\n'

        # Calculate progress statistics
        total_tasks = len(self.tasks)
        completed = sum(
            1
            for task in self.tasks
            if task.status == TaskStatus.COMPLETED  # Remove .value here
        )
        in_progress = sum(
            1
            for task in self.tasks
            if task.status == TaskStatus.IN_PROGRESS  # Remove .value here
        )
        blocked = sum(
            1
            for task in self.tasks
            if task.status == TaskStatus.BLOCKED  # Remove .value here
        )
        not_started = sum(
            1
            for task in self.tasks
            if task.status == TaskStatus.NOT_STARTED  # Remove .value here
        )

        output += f'Progress: {completed}/{total_tasks} tasks completed '
        if total_tasks > 0:
            percentage = (completed / total_tasks) * 100
            output += f'({percentage:.1f}%)\n'
        else:
            output += '(0%)\n'

        output += f'Status: {completed} completed, {in_progress} in progress, {blocked} blocked, {not_started} not started\n\n'
        output += 'Tasks:\n'

        # Add each step with its status and notes
        for i, task in enumerate(self.tasks):
            task_content = task.content
            task_status = task.status
            task_result = task.result

            # Use a mapping from TaskStatus enum to string
            status_symbol = {
                TaskStatus.NOT_STARTED: '[ ]',
                TaskStatus.IN_PROGRESS: '[→]',
                TaskStatus.COMPLETED: '[✓]',
                TaskStatus.BLOCKED: '[!]',
            }.get(task_status, '[ ]')

            task_result = task_result or ''
            task_result = task_result.strip()

            if w_result:
                output += (
                    f'{i}. {status_symbol} {task_content}\n------- task_result -------\n{task_result.strip()} \n\n'
                    if task_result
                    else f'{i}. {status_symbol} {task_content}\n\n'
                )
            else:
                output += f'{i}. {status_symbol} {task_content}\n'

        return output
