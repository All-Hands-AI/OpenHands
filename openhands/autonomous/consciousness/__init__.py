"""
L2: Consciousness Core

The system's brain - analyzes perceptions and makes autonomous decisions.

Responsibilities:
- Analyze incoming perception events
- Evaluate importance and urgency
- Decide whether action is needed
- Generate autonomous goals
- Create execution plans
"""

from openhands.autonomous.consciousness.core import ConsciousnessCore
from openhands.autonomous.consciousness.decision import Decision, DecisionType
from openhands.autonomous.consciousness.goal import Goal, GoalPriority, GoalStatus

__all__ = [
    'ConsciousnessCore',
    'Decision',
    'DecisionType',
    'Goal',
    'GoalPriority',
    'GoalStatus',
]
