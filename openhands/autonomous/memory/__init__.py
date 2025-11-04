"""
L4: Learning & Memory System

The system's experience and knowledge - learns from past actions.

Responsibilities:
- Store execution history
- Analyze success/failure patterns
- Extract reusable knowledge
- Generate microagents from learned patterns
- Optimize future decisions
"""

from openhands.autonomous.memory.memory import MemorySystem
from openhands.autonomous.memory.experience import Experience, ExperienceType

__all__ = [
    'MemorySystem',
    'Experience',
    'ExperienceType',
]
