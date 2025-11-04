"""
Decision data structures
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from openhands.autonomous.perception.base import PerceptionEvent


class DecisionType(Enum):
    """Types of decisions the system can make"""

    # Code actions
    FIX_BUG = "fix_bug"
    ADD_FEATURE = "add_feature"
    REFACTOR_CODE = "refactor_code"
    IMPROVE_TESTS = "improve_tests"
    UPDATE_DOCS = "update_docs"
    OPTIMIZE_PERFORMANCE = "optimize_performance"

    # Issue/PR actions
    RESPOND_TO_ISSUE = "respond_to_issue"
    REVIEW_PR = "review_pr"
    CREATE_PR = "create_pr"
    CLOSE_ISSUE = "close_issue"

    # Maintenance actions
    UPDATE_DEPENDENCIES = "update_dependencies"
    FIX_SECURITY_ISSUE = "fix_security_issue"
    IMPROVE_CI = "improve_ci"
    CLEANUP_CODE = "cleanup_code"

    # Learning actions
    ANALYZE_CODEBASE = "analyze_codebase"
    GENERATE_MICROAGENT = "generate_microagent"
    UPDATE_KNOWLEDGE = "update_knowledge"

    # Meta actions
    NO_ACTION = "no_action"
    DEFER = "defer"
    ESCALATE_TO_HUMAN = "escalate_to_human"


@dataclass
class Decision:
    """
    A decision made by the consciousness core

    Represents what the system has decided to do in response to events.
    """
    decision_type: DecisionType
    trigger_events: List[PerceptionEvent]
    reasoning: str  # Why this decision was made
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)

    # Execution details
    action_plan: Dict[str, Any] = field(default_factory=dict)
    estimated_effort: Optional[str] = None  # 'low', 'medium', 'high'
    requires_approval: bool = False

    # Tracking
    id: str = field(default_factory=lambda: f"dec_{datetime.now().timestamp()}")
    executed: bool = False
    outcome: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'id': self.id,
            'decision_type': self.decision_type.value,
            'trigger_events': [e.id for e in self.trigger_events],
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'action_plan': self.action_plan,
            'estimated_effort': self.estimated_effort,
            'requires_approval': self.requires_approval,
            'executed': self.executed,
            'outcome': self.outcome,
        }
