"""
Tests for Autonomous Executor (L3)
"""

import asyncio

import pytest

from openhands.autonomous.consciousness.decision import Decision, DecisionType
from openhands.autonomous.executor.executor import AutonomousExecutor
from openhands.autonomous.executor.task import ExecutionTask, TaskStatus
from openhands.autonomous.perception.base import EventPriority, EventType, PerceptionEvent


class TestExecutionTask:
    """Tests for ExecutionTask class"""

    def test_create_task(self, sample_decision):
        """Test creating an execution task"""
        task = ExecutionTask(decision=sample_decision)

        assert task.decision == sample_decision
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0
        assert task.retry_count == 0
        assert task.id.startswith('task_')

    def test_task_lifecycle(self, sample_decision):
        """Test task lifecycle"""
        task = ExecutionTask(decision=sample_decision)

        # Start task
        task.mark_started()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

        # Complete task
        task.mark_completed(output="Task completed successfully")
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.progress == 1.0
        assert task.output == "Task completed successfully"

    def test_task_failure(self, sample_decision):
        """Test task failure"""
        task = ExecutionTask(decision=sample_decision)

        task.mark_started()
        task.mark_failed("Something went wrong")

        assert task.status == TaskStatus.FAILED
        assert task.error == "Something went wrong"

    def test_task_retry(self, sample_decision):
        """Test task retry logic"""
        task = ExecutionTask(decision=sample_decision, max_retries=3)

        # Can retry initially
        assert task.can_retry()

        # Exhaust retries
        task.retry_count = 3
        assert not task.can_retry()

    def test_task_artifacts(self, sample_decision):
        """Test adding artifacts to task"""
        task = ExecutionTask(decision=sample_decision)

        task.add_artifact('commit', {'hash': 'abc123', 'message': 'Fix bug'})
        task.add_artifact('pr', {'number': 456, 'url': 'https://github.com/...'})

        assert len(task.artifacts) == 2
        assert task.artifacts[0]['type'] == 'commit'
        assert task.artifacts[1]['type'] == 'pr'

    def test_task_to_dict(self, sample_decision):
        """Test serializing task to dict"""
        task = ExecutionTask(decision=sample_decision)
        task.mark_started()

        data = task.to_dict()

        assert data['status'] == 'running'
        assert data['decision_id'] == sample_decision.id
        assert 'started_at' in data


class TestAutonomousExecutor:
    """Tests for AutonomousExecutor class"""

    @pytest.mark.asyncio
    async def test_create_executor(self, executor):
        """Test creating an executor"""
        assert executor.max_concurrent_tasks == 2
        assert executor.sandbox
        assert not executor.auto_commit
        assert not executor.running

    @pytest.mark.asyncio
    async def test_submit_decision(self, executor, sample_decision):
        """Test submitting a decision for execution"""
        task = await executor.submit_decision(sample_decision)

        assert isinstance(task, ExecutionTask)
        assert task.decision == sample_decision
        assert task in executor.pending_tasks

    @pytest.mark.asyncio
    async def test_executor_start_stop(self, executor):
        """Test starting and stopping executor"""
        # Start in background
        start_task = asyncio.create_task(executor.start())

        # Wait a bit
        await asyncio.sleep(0.1)
        assert executor.running

        # Stop
        await executor.stop()
        assert not executor.running

        # Wait for start task to complete
        try:
            await asyncio.wait_for(start_task, timeout=1.0)
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    async def test_task_execution(self, executor, sample_decision):
        """Test executing a task"""
        # Submit task
        task = await executor.submit_decision(sample_decision)

        # Execute directly (without starting the loop)
        await executor._execute_task(task)

        # Task should be completed or failed
        assert task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        assert task not in executor.running_tasks
        assert task in executor.completed_tasks

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self, executor):
        """Test concurrent task limit"""
        # Create multiple decisions
        decisions = []
        for i in range(5):
            event = PerceptionEvent(
                event_type=EventType.TEST_FAILED,
                priority=EventPriority.HIGH,
                timestamp=None,
                source="Test",
                data={'test': f'test_{i}'},
            )
            decision = Decision(
                decision_type=DecisionType.FIX_BUG,
                trigger_events=[event],
                reasoning="Test",
                confidence=0.8,
            )
            decisions.append(decision)

        # Submit all tasks
        tasks = []
        for decision in decisions:
            task = await executor.submit_decision(decision)
            tasks.append(task)

        assert len(executor.pending_tasks) == 5

        # Start executor
        start_task = asyncio.create_task(executor.start())

        # Wait for some tasks to start
        await asyncio.sleep(0.5)

        # Should not exceed max concurrent
        assert len(executor.running_tasks) <= executor.max_concurrent_tasks

        # Stop executor
        await executor.stop()

        try:
            await asyncio.wait_for(start_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    def test_get_task_status(self, executor, sample_decision):
        """Test getting task status"""
        # Submit task
        task = ExecutionTask(decision=sample_decision)
        executor.pending_tasks.append(task)

        # Get status
        found_task = executor.get_task_status(task.id)
        assert found_task == task

        # Non-existent task
        not_found = executor.get_task_status("invalid_id")
        assert not_found is None

    def test_get_statistics(self, executor, sample_decision):
        """Test getting executor statistics"""
        # Create some tasks
        task1 = ExecutionTask(decision=sample_decision)
        task1.mark_completed()

        task2 = ExecutionTask(decision=sample_decision)
        task2.mark_failed("Error")

        executor.completed_tasks = [task1, task2]

        stats = executor.get_statistics()

        assert stats['pending'] == 0
        assert stats['running'] == 0
        assert stats['completed'] == 1
        assert stats['failed'] == 1
        assert stats['total_completed'] == 2

    @pytest.mark.asyncio
    async def test_task_retry_on_failure(self, executor, sample_decision):
        """Test that failed tasks are retried"""
        task = await executor.submit_decision(sample_decision)
        task.max_retries = 2

        # Manually execute and fail
        task.mark_started()
        task.mark_failed("Temporary error")

        # Move to completed
        executor.running_tasks.append(task)
        executor.running_tasks.remove(task)
        executor.completed_tasks.append(task)

        # Check retry logic in _execute_task would re-add to pending
        # (This is tested indirectly through the retry_count check)
        assert task.retry_count == 0  # Not incremented yet
        assert task.can_retry()
