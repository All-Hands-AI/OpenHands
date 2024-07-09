import pytest

from opendevin.controller.state.task import (
    ABANDONED_STATE,
    COMPLETED_STATE,
    IN_PROGRESS_STATE,
    OPEN_STATE,
    VERIFIED_STATE,
    Task,
)
from opendevin.core.exceptions import TaskInvalidStateError


@pytest.fixture
def task():
    return Task(parent=None, goal='Task Goal')


@pytest.fixture
def task_with_subtasks(task: Task):
    subtask1 = Task(parent=task, goal='Subtask Goal 1')
    subtask2 = Task(parent=task, goal='Subtask Goal 2')

    task.subtasks.append(subtask1)
    task.subtasks.append(subtask2)
    return task


class TestTaskInitialisation:
    def test_task_initialisation(self, task: Task):
        assert task.id == '0', 'The initial parent task id should be 0'
        assert task.goal == 'Task Goal'
        assert task.state == OPEN_STATE, 'The initial parent task state should be open'
        assert task.subtasks == [], 'The initial parent task should have no subtasks'
        assert task.parent is None

    def test_task_to_dict(self, task: Task):
        expected_dict = {
            'id': '0',
            'goal': 'Task Goal',
            'state': 'open',
            'subtasks': [],
        }

        assert task.to_dict() == expected_dict

    def test_get_current_task(self, task: Task):
        assert (
            task.get_current_task() is None
        ), 'The current task should be none if it is not in progress'

        task.set_state(IN_PROGRESS_STATE)
        assert (
            task.get_current_task() == task
        ), 'The current task should be itself if it is in progress'


class TestTaskState:
    def test_initial_state(self, task: Task):
        assert task.state == OPEN_STATE, 'The initial state should be open'

    def test_set_state(self, task: Task):
        task.set_state(VERIFIED_STATE)
        assert task.state == VERIFIED_STATE, 'The state should be set to verified'

        task.set_state(COMPLETED_STATE)
        assert task.state == COMPLETED_STATE, 'The state should be set to completed'

    def test_set_state_error(self, task: Task):
        with pytest.raises(TaskInvalidStateError):
            task.set_state('invalid_state')


class TestTaskToString:
    def test_initial_task_to_string(self, task: Task):
        expected_string = '🔵 0 Task Goal\n'
        assert (
            task.to_string() == expected_string
        ), 'It should initialise with an open state'

    def test_open_task_to_string(self, task: Task):
        expected_string = '🔵 0 Task Goal\n'
        assert (
            task.to_string() == expected_string
        ), 'It should initialise with an open state'

    def test_verified_task_to_string(self, task: Task):
        task.set_state(VERIFIED_STATE)
        expected_string = '✅ 0 Task Goal\n'
        assert (
            task.to_string() == expected_string
        ), 'It should change to a verified state'

    def test_completed_task_to_string(self, task: Task):
        task.set_state(COMPLETED_STATE)
        expected_string = '🟢 0 Task Goal\n'
        assert (
            task.to_string() == expected_string
        ), 'It should change to a completed state'

    def test_abandoned_task_to_string(self, task: Task):
        task.set_state(ABANDONED_STATE)
        expected_string = '❌ 0 Task Goal\n'
        assert (
            task.to_string() == expected_string
        ), 'It should change to an abandoned state'

    def test_in_progress_task_to_string(self, task: Task):
        task.set_state(IN_PROGRESS_STATE)
        expected_string = '💪 0 Task Goal\n'
        assert (
            task.to_string() == expected_string
        ), 'It should change to an in progress state'


class TestTaskSubtask:
    @pytest.mark.xfail(reason='parent task does not update')
    def test_task_initialises_with_subtasks(self, task: Task):
        task = Task(parent=task, goal='Subtask Goal')
        assert task.parent == task, 'The parent task should be set'
        assert task.subtasks == [task], 'The subtask should be added to the parent task'

    def test_task_initialises_with_subtasks_alt(self, task_with_subtasks: Task):
        assert (
            len(task_with_subtasks.subtasks) == 2
        ), 'The parent task should have two subtasks'
        assert (
            task_with_subtasks.subtasks[0].parent == task_with_subtasks
        ), 'The parent task should be set'

    @pytest.mark.xfail(reason='subtasks have incorrect ids')
    def test_to_dict(self, task_with_subtasks: Task):
        expected_dict = {
            'id': '0',
            'goal': 'Task Goal',
            'state': 'open',
            'subtasks': [
                {
                    'id': '0.0',
                    'goal': 'Subtask Goal 1',
                    'state': 'open',
                    'subtasks': [],
                },
                {
                    'id': '0.1',
                    'goal': 'Subtask Goal 2',
                    'state': 'open',
                    'subtasks': [],
                },
            ],
        }

        assert task_with_subtasks.to_dict() == expected_dict
