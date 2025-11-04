"""
L5: Lifecycle Manager

The system's life force - keeps the system alive and healthy.

Responsibilities:
- System bootstrapping and initialization
- Health monitoring and self-healing
- Resource management
- Sleep/wake cycles
- Version evolution
"""

from openhands.autonomous.lifecycle.manager import LifecycleManager
from openhands.autonomous.lifecycle.health import HealthStatus

__all__ = [
    'LifecycleManager',
    'HealthStatus',
]
