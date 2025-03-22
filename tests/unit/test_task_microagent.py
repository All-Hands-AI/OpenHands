import tempfile
from pathlib import Path

import pytest

from openhands.microagent.microagent import TaskMicroAgent
from openhands.microagent.types import MicroAgentMetadata, MicroAgentType


@pytest.fixture
def task_agent():
    return TaskMicroAgent(
        name='test_task',
        content='Test task content',
        metadata=MicroAgentMetadata(
            name='test_task',
            type=MicroAgentType.TASK,
            version='1.0.0',
            agent='CodeActAgent',
        ),
        source='test_source',
        type=MicroAgentType.TASK,
    )


def test_create_progress_file(task_agent):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        title = 'Test Task'
        description = 'A test task description'
        steps = [
            'Step 1',
            {'Step 2': ['Subtask 2.1', 'Subtask 2.2']},
            'Step 3',
        ]

        file_path = task_agent.create_progress_file(
            title, description, steps, output_dir
        )

        assert file_path.exists()
        content = file_path.read_text()

        # Check basic content structure
        assert '# Test Task' in content
        assert 'A test task description' in content
        assert '## Task Steps' in content
        assert '- [ ] 1. Step 1' in content
        assert '- [ ] 2. Step 2' in content
        assert '    - [ ] 2.1. Subtask 2.1' in content
        assert '    - [ ] 2.2. Subtask 2.2' in content
        assert '- [ ] 3. Step 3' in content
        assert '## Review Notes' in content
        assert '_No review notes yet._' in content
        assert 'Task Status: In Progress' in content


def test_update_step_status(task_agent):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        title = 'Test Task'
        description = 'A test task description'
        steps = [
            'Step 1',
            {'Step 2': ['Subtask 2.1', 'Subtask 2.2']},
        ]

        file_path = task_agent.create_progress_file(
            title, description, steps, output_dir
        )

        # Test main step completion
        task_agent.update_step_status(1, True, file_path)
        content = file_path.read_text()
        assert '- [x] 1. Step 1' in content
        assert '- [ ] 2. Step 2' in content

        # Test subtask completion
        task_agent.update_step_status(2, True, file_path, subtask_index=1)
        content = file_path.read_text()
        assert '    - [x] 2.1. Subtask 2.1' in content
        assert '    - [ ] 2.2. Subtask 2.2' in content


def test_add_review_notes(task_agent):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        title = 'Test Task'
        description = 'A test task description'
        steps = ['Step 1']

        file_path = task_agent.create_progress_file(
            title, description, steps, output_dir
        )
        task_agent.add_review_notes('Test review notes', file_path)

        content = file_path.read_text()
        assert 'Test review notes' in content
        assert '_No review notes yet._' not in content


def test_mark_completed(task_agent):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        title = 'Test Task'
        description = 'A test task description'
        steps = ['Step 1']

        file_path = task_agent.create_progress_file(
            title, description, steps, output_dir
        )
        task_agent.mark_completed(file_path)

        content = file_path.read_text()
        assert 'Task Status: Completed' in content


def test_invalid_step_index(task_agent):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        title = 'Test Task'
        description = 'A test task description'
        steps = [
            'Step 1',
            {'Step 2': ['Subtask 2.1']},
        ]

        file_path = task_agent.create_progress_file(
            title, description, steps, output_dir
        )

        # Test invalid main step index
        with pytest.raises(ValueError, match='Invalid step index 3'):
            task_agent.update_step_status(3, True, file_path)

        # Test invalid subtask index
        with pytest.raises(ValueError, match='Invalid subtask index 2 for step 2'):
            task_agent.update_step_status(2, True, file_path, subtask_index=2)

        # Test subtask on step without subtasks
        with pytest.raises(ValueError, match='Step 1 has no subtasks'):
            task_agent.update_step_status(1, True, file_path, subtask_index=1)


def test_operations_without_progress_file(task_agent):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / 'nonexistent.md'
        with pytest.raises(ValueError, match='No task progress being tracked'):
            task_agent.update_step_status(1, True, file_path)
        with pytest.raises(ValueError, match='No task progress being tracked'):
            task_agent.add_review_notes('Test notes', file_path)
        with pytest.raises(ValueError, match='No task progress being tracked'):
            task_agent.mark_completed(file_path)


def test_invalid_step_format(task_agent):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        title = 'Test Task'
        description = 'A test task description'

        # Test with invalid step type
        steps = [42]  # Integer instead of string or dict
        with pytest.raises(
            ValueError,
            match='Each step must be either a string or a dict with subtasks',
        ):
            task_agent.create_progress_file(title, description, steps, output_dir)

        # Test with empty dict
        steps = [{}]
        with pytest.raises(
            ValueError,
            match='Each step must be either a string or a dict with subtasks',
        ):
            task_agent.create_progress_file(title, description, steps, output_dir)

        # Test with dict containing non-list value
        steps = [{'Step 1': 'not a list'}]
        with pytest.raises(
            ValueError,
            match='Each step must be either a string or a dict with subtasks',
        ):
            task_agent.create_progress_file(title, description, steps, output_dir)
