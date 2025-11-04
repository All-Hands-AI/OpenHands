"""
Health monitoring
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Overall health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class SystemHealth:
    """System health snapshot"""
    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float

    # Component health
    perception_active: bool
    consciousness_active: bool
    executor_active: bool
    memory_accessible: bool

    # Resource usage
    memory_mb: float
    cpu_percent: float

    # Activity metrics
    events_processed: int
    decisions_made: int
    tasks_completed: int
    tasks_failed: int

    def to_dict(self):
        """Serialize to dict"""
        return {
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'uptime_seconds': self.uptime_seconds,
            'components': {
                'perception': self.perception_active,
                'consciousness': self.consciousness_active,
                'executor': self.executor_active,
                'memory': self.memory_accessible,
            },
            'resources': {
                'memory_mb': self.memory_mb,
                'cpu_percent': self.cpu_percent,
            },
            'metrics': {
                'events_processed': self.events_processed,
                'decisions_made': self.decisions_made,
                'tasks_completed': self.tasks_completed,
                'tasks_failed': self.tasks_failed,
            },
        }
