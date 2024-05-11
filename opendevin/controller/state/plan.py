from opendevin.core.exceptions import (
    AgentMalformedActionError,
    PlanInvalidStateError,
)
from opendevin.core.logger import opendevin_logger as logger

OPEN_STATE = 'open'
COMPLETED_STATE = 'completed'
ABANDONED_STATE = 'abandoned'
IN_PROGRESS_STATE = 'in_progress'
VERIFIED_STATE = 'verified'
STATES = [
    OPEN_STATE,
    COMPLETED_STATE,
    ABANDONED_STATE,
    IN_PROGRESS_STATE,
    VERIFIED_STATE,
]


class Task:
    id: str
    goal: str
    parent: 'Task | None'
    subtasks: list['Task']

    def __init__(
        self,
        parent: 'Task',
        goal: str,
        state: str = OPEN_STATE,
        subtasks: list = [],
    ):
        """Initializes a new instance of the Task class.

        Args:
            parent: The parent task, or None if it is the root task.
            goal: The goal of the task.
            state: The initial state of the task.
            subtasks: A list of subtasks associated with this task.
        """
        if parent.id:
            self.id = parent.id + '.' + str(len(parent.subtasks))
        else:
            self.id = str(len(parent.subtasks))
        self.parent = parent
        self.goal = goal
        self.subtasks = []
        for subtask in subtasks or []:
            if isinstance(subtask, Task):
                self.subtasks.append(subtask)
            else:
                goal = subtask.get('goal')
                state = subtask.get('state')
                subtasks = subtask.get('subtasks')
                self.subtasks.append(Task(self, goal, state, subtasks))

        self.state = OPEN_STATE

    def to_string(self, indent=''):
        """Returns a string representation of the task and its subtasks.

        Args:
            indent: The indentation string for formatting the output.

        Returns:
            A string representation of the task and its subtasks.
        """
        emoji = ''
        if self.state == VERIFIED_STATE:
            emoji = '✅'
        elif self.state == COMPLETED_STATE:
            emoji = '🟢'
        elif self.state == ABANDONED_STATE:
            emoji = '❌'
        elif self.state == IN_PROGRESS_STATE:
            emoji = '💪'
        elif self.state == OPEN_STATE:
            emoji = '🔵'
        result = indent + emoji + ' ' + self.id + ' ' + self.goal + '\n'
        for subtask in self.subtasks:
            result += subtask.to_string(indent + '    ')
        return result

    def to_dict(self):
        """Returns a dictionary representation of the task.

        Returns:
            A dictionary containing the task's attributes.
        """
        return {
            'id': self.id,
            'goal': self.goal,
            'state': self.state,
            'subtasks': [t.to_dict() for t in self.subtasks],
        }

    def set_state(self, state):
        """Sets the state of the task and its subtasks.

        Args:            state: The new state of the task.

        Raises:
            PlanInvalidStateError: If the provided state is invalid.
        """
        if state not in STATES:
            logger.error('Invalid state: %s', state)
            raise PlanInvalidStateError(state)
        self.state = state
        if (
            state == COMPLETED_STATE
            or state == ABANDONED_STATE
            or state == VERIFIED_STATE
        ):
            for subtask in self.subtasks:
                if subtask.state != ABANDONED_STATE:
                    subtask.set_state(state)
        elif state == IN_PROGRESS_STATE:
            if self.parent is not None:
                self.parent.set_state(state)

    def get_current_task(self) -> 'Task | None':
        """Retrieves the current task in progress.

        Returns:
            The current task in progress, or None if no task is in progress.
        """
        for subtask in self.subtasks:
            if subtask.state == IN_PROGRESS_STATE:
                return subtask.get_current_task()
        if self.state == IN_PROGRESS_STATE:
            return self
        return None


class Plan(Task):
    """Serves as the root node in a tree of tasks.
    Because we want the top-level of the plan to be a list of tasks (1, 2, 3, etc.),
    the "root node" of the data structure is kind of invisible--it just
    holds references to the top-level tasks.

    Attributes:
        id: Kept blank for plan
        goal: Kept blank for plan
        parent: None for plan
        subtasks: The top-level list of tasks associated with the plan.
        state: The state of the plan.
    """

    id: str = ''
    goal: str = ''
    parent: None = None

    def __init__(self):
        self.subtasks = []
        self.state = OPEN_STATE

    def __str__(self):
        """Returns a string representation of the plan.

        Returns:
            A string representation of the plan.
        """
        return self.to_string()

    def get_task_by_id(self, id: str) -> Task:
        """Retrieves a task by its ID.

        Args:
            id: The ID of the task.

        Returns:
            The task with the specified ID.

        Raises:
            AgentMalformedActionError: If the provided task ID is invalid or does not exist.
        """
        if id == '':
            return self
        if len(self.subtasks) == 0:
            raise AgentMalformedActionError('Task does not exist:' + id)
        try:
            parts = [int(p) for p in id.split('.')]
        except ValueError:
            raise AgentMalformedActionError('Invalid task id:' + id)
        task: Task = self
        for part in parts:
            if part >= len(task.subtasks):
                raise AgentMalformedActionError('Task does not exist:' + id)
            task = task.subtasks[part]
        return task

    def add_subtask(self, parent_id: str, goal: str, subtasks: list = []):
        """Adds a subtask to a parent task.

        Args:
            parent_id: The ID of the parent task.
            goal: The goal of the subtask.
            subtasks: A list of subtasks associated with the new subtask.
        """
        parent = self.get_task_by_id(parent_id)
        child = Task(parent=parent, goal=goal, subtasks=subtasks)
        parent.subtasks.append(child)

    def set_subtask_state(self, id: str, state: str):
        """Sets the state of a subtask.

        Args:
            id: The ID of the subtask.
            state: The new state of the subtask.
        """
        task = self.get_task_by_id(id)
        task.set_state(state)
