"""
Execution task data structures
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from openhands.autonomous.consciousness.decision import Decision


class TaskStatus(Enum):
    """Status of an execution task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionTask:
    """
    A task to be executed

    Wraps a Decision with execution tracking.
    """
    decision: Decision

    # Execution tracking
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0

    # Results
    output: Optional[str] = None
    error: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)  # Files, commits, PRs, etc.

    # Metadata
    id: str = field(default_factory=lambda: f"task_{datetime.now().timestamp()}")
    retry_count: int = 0
    max_retries: int = 3

    def mark_started(self):
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, output: Optional[str] = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 1.0
        if output:
            self.output = output

    def mark_failed(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries

    def add_artifact(self, artifact_type: str, data: Dict[str, Any]):
        """Add an artifact produced by this task"""
        self.artifacts.append({
            'type': artifact_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
        })

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'id': self.id,
            'decision_id': self.decision.id,
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'output': self.output,
            'error': self.error,
            'artifacts': self.artifacts,
            'retry_count': self.retry_count,
        }
