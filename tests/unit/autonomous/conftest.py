"""
Pytest fixtures for autonomous system tests
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from openhands.autonomous.consciousness.core import ConsciousnessCore
from openhands.autonomous.consciousness.decision import Decision, DecisionType
from openhands.autonomous.executor.executor import AutonomousExecutor
from openhands.autonomous.executor.task import ExecutionTask, TaskStatus
from openhands.autonomous.lifecycle.manager import LifecycleManager
from openhands.autonomous.memory.experience import Experience, ExperienceType
from openhands.autonomous.memory.memory import MemorySystem
from openhands.autonomous.perception.base import (
    EventPriority,
    EventType,
    PerceptionEvent,
    PerceptionLayer,
)


@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_repo(temp_dir: Path) -> Path:
    """Create a temporary git repository"""
    import subprocess

    repo_path = temp_dir / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        capture_output=True,
    )

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
    )

    return repo_path


@pytest.fixture
def temp_db(temp_dir: Path) -> Path:
    """Create a temporary database path"""
    return temp_dir / "test_memory.db"


@pytest.fixture
def sample_perception_event() -> PerceptionEvent:
    """Create a sample perception event"""
    return PerceptionEvent(
        event_type=EventType.TEST_FAILED,
        priority=EventPriority.HIGH,
        timestamp=datetime.now(),
        source="TestMonitor",
        data={
            'test_name': 'test_sample',
            'error_message': 'AssertionError: Expected True, got False',
        },
    )


@pytest.fixture
def sample_git_commit_event() -> PerceptionEvent:
    """Create a sample git commit event"""
    return PerceptionEvent(
        event_type=EventType.GIT_COMMIT,
        priority=EventPriority.MEDIUM,
        timestamp=datetime.now(),
        source="GitMonitor",
        data={
            'branch': 'main',
            'commit': {
                'hash': 'abc123',
                'message': 'Fix bug in parser',
                'author': 'Test User',
                'files_changed': ['parser.py', 'tests/test_parser.py'],
                'file_count': 2,
            },
        },
    )


@pytest.fixture
def sample_issue_event() -> PerceptionEvent:
    """Create a sample GitHub issue event"""
    return PerceptionEvent(
        event_type=EventType.GITHUB_ISSUE_OPENED,
        priority=EventPriority.HIGH,
        timestamp=datetime.now(),
        source="GitHubMonitor",
        data={
            'issue_number': 123,
            'title': 'Bug: Application crashes on startup',
            'author': 'user123',
            'body': 'When I start the app, it crashes immediately.',
            'labels': ['bug', 'critical'],
            'url': 'https://github.com/test/repo/issues/123',
        },
    )


@pytest.fixture
def sample_decision(sample_perception_event: PerceptionEvent) -> Decision:
    """Create a sample decision"""
    return Decision(
        decision_type=DecisionType.FIX_BUG,
        trigger_events=[sample_perception_event],
        reasoning="Tests are failing and need to be fixed",
        confidence=0.8,
        action_plan={
            'task': 'Fix failing tests',
            'steps': ['Analyze error', 'Fix code', 'Verify tests pass'],
        },
        estimated_effort='medium',
        requires_approval=False,
    )


@pytest.fixture
def sample_experience() -> Experience:
    """Create a sample experience"""
    return Experience(
        experience_type=ExperienceType.BUG_FIX,
        timestamp=datetime.now(),
        trigger="test_failed decision",
        context={'test_name': 'test_sample'},
        action_taken="Fixed the failing test",
        reasoning="Test was failing due to assertion error",
        success=True,
        outcome_description="Test now passes",
        confidence=0.8,
    )


@pytest.fixture
async def perception_layer() -> PerceptionLayer:
    """Create a perception layer instance"""
    return PerceptionLayer()


@pytest.fixture
def consciousness_core() -> ConsciousnessCore:
    """Create a consciousness core instance"""
    return ConsciousnessCore(autonomy_level='medium', auto_approve=False)


@pytest.fixture
async def executor() -> AutonomousExecutor:
    """Create an executor instance"""
    return AutonomousExecutor(
        max_concurrent_tasks=2,
        sandbox=True,
        auto_commit=False,
        auto_pr=False,
    )


@pytest.fixture
def memory_system(temp_db: Path) -> MemorySystem:
    """Create a memory system instance"""
    return MemorySystem(db_path=str(temp_db))


@pytest.fixture
async def lifecycle_manager(temp_repo: Path) -> LifecycleManager:
    """Create a lifecycle manager instance"""
    manager = LifecycleManager(
        repo_path=str(temp_repo),
        health_check_interval=1,
        max_memory_mb=1024,
        max_cpu_percent=90.0,
    )
    await manager.initialize()
    return manager
