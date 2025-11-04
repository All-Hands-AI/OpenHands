"""
L3: Autonomous Executor

The system's muscles - executes decisions autonomously.

Responsibilities:
- Execute approved decisions
- Coordinate with OpenHands agent system
- Track execution progress
- Report results
"""

from openhands.autonomous.executor.executor import AutonomousExecutor
from openhands.autonomous.executor.task import ExecutionTask, TaskStatus

__all__ = [
    'AutonomousExecutor',
    'ExecutionTask',
    'TaskStatus',
]
