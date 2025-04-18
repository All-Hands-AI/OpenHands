from dataclasses import dataclass

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class CreatePlanAction(Action):
    """An action where the agent creates a plan.

    Attributes:
        plan_id (str): The ID of the plan.
        title (str): The title of the plan.
        tasks (list[str]): The tasks of the plan.
        action (str): The action type, namely ActionType.PLAN.
    """

    plan_id: str
    title: str
    tasks: list[str]
    action: str = ActionType.CREATE_PLAN

    @property
    def message(self) -> str:
        return f'Created a plan with title {self.title} and tasks {self.tasks}'


@dataclass
class TaskStatus:
    """The status of a task."""

    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    BLOCKED = 'blocked'

    @classmethod
    def get_active_statuses(cls) -> list[str]:
        """Return a list of values representing active statuses (not started or in progress)"""
        return [cls.NOT_STARTED, cls.IN_PROGRESS]

    @classmethod
    def get_status_marks(cls) -> dict[str, str]:
        """Return a mapping of statuses to their marker symbols"""
        return {
            cls.COMPLETED: '[✓]',
            cls.IN_PROGRESS: '[→]',
            cls.BLOCKED: '[!]',
            cls.NOT_STARTED: '[ ]',
        }


@dataclass
class MarkTaskAction(Action):
    """An action where the agent updates a plan.

    Attributes:
        plan_id (str): The ID of the plan.
        task_index (int): The index of the task to mask.
        task_status (TaskStatus): The status of the task.
        task_result (str): The result of the task.
        action (str): The action type, namely ActionType.PLAN.
    """

    plan_id: str
    task_index: int
    task_status: str
    task_content: str = ''
    task_result: str = ''
    action: str = ActionType.MASK_TASK

    @property
    def message(self) -> str:
        return self.task_content


@dataclass
class AssignTaskAction(Action):
    """An action where the agent assigns a task to a delegate.

    Attributes:
        plan_id (str): The ID of the plan.
        task_index (int): The index of the task to assign.
        delegate_id (str): The ID of the delegate.
        action (str): The action type, namely ActionType.PLAN.
    """

    plan_id: str
    task_index: int
    task_content: str
    delegate_id: str
    action: str = ActionType.ASIGN_TASK

    @property
    def message(self) -> str:
        return f'Assigned task {self.task_index}. {self.task_content} in plan {self.plan_id} to delegate {self.delegate_id}'
