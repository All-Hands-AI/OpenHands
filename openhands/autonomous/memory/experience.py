"""
Experience data structures

Experiences are learned from execution outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExperienceType(Enum):
    """Types of experiences"""
    BUG_FIX = "bug_fix"
    FEATURE_ADDITION = "feature_addition"
    REFACTORING = "refactoring"
    TEST_IMPROVEMENT = "test_improvement"
    DOCUMENTATION = "documentation"
    ISSUE_RESPONSE = "issue_response"
    DEPENDENCY_UPDATE = "dependency_update"
    SECURITY_FIX = "security_fix"


@dataclass
class Experience:
    """
    A learned experience from execution

    Captures what was done, why, and the outcome.
    """
    experience_type: ExperienceType
    timestamp: datetime

    # Context
    trigger: str  # What caused this
    context: Dict[str, Any]  # Environmental context

    # Action
    action_taken: str  # What we did
    reasoning: str  # Why we did it

    # Outcome
    success: bool
    outcome_description: str
    artifacts: List[Dict[str, Any]] = field(default_factory=list)

    # Learning
    lessons_learned: List[str] = field(default_factory=list)
    confidence: float = 0.0  # How confident we are in this experience
    reusability_score: float = 0.0  # How reusable is this pattern (0-1)

    # Metadata
    id: str = field(default_factory=lambda: f"exp_{datetime.now().timestamp()}")
    tags: List[str] = field(default_factory=list)
    related_experiences: List[str] = field(default_factory=list)

    def add_lesson(self, lesson: str):
        """Add a lesson learned"""
        self.lessons_learned.append(lesson)

    def calculate_reusability(self) -> float:
        """
        Calculate how reusable this experience is

        Higher score means this pattern can be applied to similar situations.
        """
        score = 0.0

        # Successful experiences are more reusable
        if self.success:
            score += 0.3

        # More specific lessons increase reusability
        score += min(len(self.lessons_learned) * 0.1, 0.3)

        # Higher confidence increases reusability
        score += self.confidence * 0.4

        self.reusability_score = min(score, 1.0)
        return self.reusability_score

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'id': self.id,
            'experience_type': self.experience_type.value,
            'timestamp': self.timestamp.isoformat(),
            'trigger': self.trigger,
            'context': self.context,
            'action_taken': self.action_taken,
            'reasoning': self.reasoning,
            'success': self.success,
            'outcome_description': self.outcome_description,
            'artifacts': self.artifacts,
            'lessons_learned': self.lessons_learned,
            'confidence': self.confidence,
            'reusability_score': self.reusability_score,
            'tags': self.tags,
            'related_experiences': self.related_experiences,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experience':
        """Deserialize from dict"""
        return cls(
            id=data['id'],
            experience_type=ExperienceType(data['experience_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            trigger=data['trigger'],
            context=data['context'],
            action_taken=data['action_taken'],
            reasoning=data['reasoning'],
            success=data['success'],
            outcome_description=data['outcome_description'],
            artifacts=data['artifacts'],
            lessons_learned=data['lessons_learned'],
            confidence=data['confidence'],
            reusability_score=data['reusability_score'],
            tags=data['tags'],
            related_experiences=data['related_experiences'],
        )
