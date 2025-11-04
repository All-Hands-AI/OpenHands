"""
Goal data structures

Goals are higher-level objectives the system sets for itself.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class GoalPriority(Enum):
    """Priority of a goal"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class GoalStatus(Enum):
    """Status of a goal"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class Goal:
    """
    A self-generated goal

    Unlike reactive decisions, goals are proactive objectives the system
    creates for itself to continuously improve.
    """
    title: str
    description: str
    priority: GoalPriority
    status: GoalStatus = GoalStatus.PENDING

    # Time tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress tracking
    progress: float = 0.0  # 0.0 to 1.0
    subtasks: List[str] = field(default_factory=list)
    completed_subtasks: List[str] = field(default_factory=list)

    # Metadata
    id: str = field(default_factory=lambda: f"goal_{datetime.now().timestamp()}")
    tags: List[str] = field(default_factory=list)

    def mark_started(self):
        """Mark goal as started"""
        self.status = GoalStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def mark_completed(self, success: bool = True):
        """Mark goal as completed or failed"""
        self.status = GoalStatus.COMPLETED if success else GoalStatus.FAILED
        self.completed_at = datetime.now()
        self.progress = 1.0 if success else self.progress

    def add_subtask(self, subtask: str):
        """Add a subtask"""
        self.subtasks.append(subtask)

    def complete_subtask(self, subtask: str):
        """Mark a subtask as completed"""
        if subtask in self.subtasks and subtask not in self.completed_subtasks:
            self.completed_subtasks.append(subtask)
            self.progress = len(self.completed_subtasks) / len(self.subtasks)

    def to_dict(self):
        """Serialize to dict"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'subtasks': self.subtasks,
            'completed_subtasks': self.completed_subtasks,
            'tags': self.tags,
        }
