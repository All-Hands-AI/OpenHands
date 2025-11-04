"""
Consciousness Core - The system's decision-making brain
"""

import asyncio
import logging
from typing import List, Optional

from openhands.autonomous.consciousness.decision import Decision, DecisionType
from openhands.autonomous.consciousness.goal import Goal, GoalPriority, GoalStatus
from openhands.autonomous.perception.base import EventPriority, EventType, PerceptionEvent

logger = logging.getLogger(__name__)


class ConsciousnessCore:
    """
    L2: Consciousness Core

    The brain of the autonomous system. Analyzes events, makes decisions,
    and generates goals.
    """

    def __init__(self, autonomy_level: str = 'medium', auto_approve: bool = False):
        """
        Args:
            autonomy_level: 'low', 'medium', or 'high'
            auto_approve: Whether to auto-approve decisions
        """
        self.autonomy_level = autonomy_level
        self.auto_approve = auto_approve

        # Active goals
        self.active_goals: List[Goal] = []
        self.completed_goals: List[Goal] = []

        # Decision history
        self.decisions: List[Decision] = []

        # Configure autonomy thresholds
        self._configure_autonomy()

    def _configure_autonomy(self):
        """Configure autonomy based on level"""
        if self.autonomy_level == 'low':
            self.min_confidence = 0.8  # High confidence required
            self.max_auto_decisions_per_hour = 5
            self.requires_approval_threshold = 0.6  # Most need approval
        elif self.autonomy_level == 'medium':
            self.min_confidence = 0.6  # Medium confidence
            self.max_auto_decisions_per_hour = 20
            self.requires_approval_threshold = 0.8  # High-risk needs approval
        else:  # high
            self.min_confidence = 0.4  # Lower confidence acceptable
            self.max_auto_decisions_per_hour = 100
            self.requires_approval_threshold = 0.9  # Very few need approval

    async def process_event(self, event: PerceptionEvent) -> Optional[Decision]:
        """
        Process a perception event and decide what to do

        Args:
            event: Event to process

        Returns:
            Decision, or None if no action needed
        """
        logger.info(f"Processing event: {event.event_type.value} (priority: {event.priority.name})")

        # Analyze the event
        decision = await self._analyze_and_decide(event)

        if decision:
            logger.info(f"Decision made: {decision.decision_type.value} (confidence: {decision.confidence:.2f})")
            self.decisions.append(decision)

        return decision

    async def _analyze_and_decide(self, event: PerceptionEvent) -> Optional[Decision]:
        """
        Analyze an event and make a decision

        This is the core intelligence of the system.
        """
        # Map event types to decision types
        decision_map = {
            EventType.TEST_FAILED: self._decide_on_test_failure,
            EventType.BUILD_FAILED: self._decide_on_build_failure,
            EventType.GITHUB_ISSUE_OPENED: self._decide_on_new_issue,
            EventType.GITHUB_PR_OPENED: self._decide_on_new_pr,
            EventType.GIT_COMMIT: self._decide_on_commit,
            EventType.DEPENDENCY_OUTDATED: self._decide_on_outdated_deps,
            EventType.SECURITY_VULNERABILITY: self._decide_on_security_issue,
        }

        # Get appropriate decision function
        decision_func = decision_map.get(event.event_type)
        if not decision_func:
            logger.debug(f"No decision logic for event type: {event.event_type.value}")
            return None

        # Make decision
        return await decision_func(event)

    async def _decide_on_test_failure(self, event: PerceptionEvent) -> Optional[Decision]:
        """Decide what to do about test failures"""
        # High priority: Tests are failing
        decision = Decision(
            decision_type=DecisionType.FIX_BUG,
            trigger_events=[event],
            reasoning="Tests are failing and need to be fixed to maintain code quality",
            confidence=0.8,
            action_plan={
                'task': 'Fix failing tests',
                'steps': [
                    'Analyze test output',
                    'Identify root cause',
                    'Fix the issue',
                    'Verify tests pass',
                ],
            },
            estimated_effort='medium',
            requires_approval=not self.auto_approve,
        )

        return decision

    async def _decide_on_build_failure(self, event: PerceptionEvent) -> Optional[Decision]:
        """Decide what to do about build failures"""
        decision = Decision(
            decision_type=DecisionType.FIX_BUG,
            trigger_events=[event],
            reasoning="Build is failing, preventing deployment and development",
            confidence=0.9,
            action_plan={
                'task': 'Fix build failure',
                'steps': [
                    'Analyze build output',
                    'Identify broken dependencies or code',
                    'Fix the issue',
                    'Verify build succeeds',
                ],
            },
            estimated_effort='high',
            requires_approval=not self.auto_approve,
        )

        return decision

    async def _decide_on_new_issue(self, event: PerceptionEvent) -> Optional[Decision]:
        """Decide what to do about a new GitHub issue"""
        issue_data = event.data

        # Analyze labels to determine if we should act
        labels = issue_data.get('labels', [])

        # Determine if this is something we can handle
        auto_labels = ['bug', 'documentation', 'good first issue', 'dependencies']
        can_handle = any(label.lower() in auto_labels for label in labels)

        if not can_handle:
            logger.info(f"Issue #{issue_data['issue_number']} doesn't match auto-handle criteria")
            return None

        decision = Decision(
            decision_type=DecisionType.RESPOND_TO_ISSUE,
            trigger_events=[event],
            reasoning=f"New issue #{issue_data['issue_number']} matches auto-handle criteria: {labels}",
            confidence=0.6,
            action_plan={
                'task': 'Respond to and potentially fix issue',
                'issue_number': issue_data['issue_number'],
                'steps': [
                    'Analyze issue description',
                    'Reproduce if possible',
                    'Propose solution or ask for clarification',
                    'Implement fix if confident',
                ],
            },
            estimated_effort='medium',
            requires_approval=True,  # Always require approval for external interactions
        )

        return decision

    async def _decide_on_new_pr(self, event: PerceptionEvent) -> Optional[Decision]:
        """Decide what to do about a new pull request"""
        # For now, just acknowledge
        # In future, could do code review
        logger.info("New PR detected, will monitor")
        return None

    async def _decide_on_commit(self, event: PerceptionEvent) -> Optional[Decision]:
        """Decide what to do about a new commit"""
        commit_data = event.data.get('commit', {})
        message = commit_data.get('message', '').lower()

        # Look for opportunities to add tests or docs
        if 'fix' in message or 'bug' in message:
            # Bug fix might need tests
            decision = Decision(
                decision_type=DecisionType.IMPROVE_TESTS,
                trigger_events=[event],
                reasoning="Bug fix commit detected, should ensure tests cover this case",
                confidence=0.5,
                action_plan={
                    'task': 'Add tests for bug fix',
                    'commit_hash': commit_data.get('hash'),
                },
                estimated_effort='low',
                requires_approval=True,
            )
            return decision

        # Low confidence, might not act
        return None

    async def _decide_on_outdated_deps(self, event: PerceptionEvent) -> Optional[Decision]:
        """Decide what to do about outdated dependencies"""
        decision = Decision(
            decision_type=DecisionType.UPDATE_DEPENDENCIES,
            trigger_events=[event],
            reasoning="Dependencies are outdated and should be updated for security and features",
            confidence=0.7,
            action_plan={
                'task': 'Update outdated dependencies',
                'packages': event.data.get('packages', []),
                'steps': [
                    'Review changelogs for breaking changes',
                    'Update dependencies',
                    'Run tests',
                    'Create PR with updates',
                ],
            },
            estimated_effort='medium',
            requires_approval=True,
        )

        return decision

    async def _decide_on_security_issue(self, event: PerceptionEvent) -> Optional[Decision]:
        """Decide what to do about security vulnerabilities"""
        decision = Decision(
            decision_type=DecisionType.FIX_SECURITY_ISSUE,
            trigger_events=[event],
            reasoning="Security vulnerability detected, must be fixed immediately",
            confidence=0.95,
            action_plan={
                'task': 'Fix security vulnerability',
                'vulnerability': event.data,
                'steps': [
                    'Assess severity and impact',
                    'Update vulnerable dependency',
                    'Test thoroughly',
                    'Deploy ASAP',
                ],
            },
            estimated_effort='high',
            requires_approval=not self.auto_approve,  # Can auto-fix in high autonomy mode
        )

        return decision

    async def generate_proactive_goals(self) -> List[Goal]:
        """
        Generate proactive goals for self-improvement

        This is where the system becomes truly autonomous - setting its own objectives.
        """
        new_goals = []

        # Goal 1: Improve code quality
        if not any(g.title == "Improve code quality" for g in self.active_goals):
            goal = Goal(
                title="Improve code quality",
                description="Continuously refactor and optimize codebase",
                priority=GoalPriority.MEDIUM,
                tags=['quality', 'refactoring'],
            )
            goal.add_subtask("Identify code duplication")
            goal.add_subtask("Improve test coverage")
            goal.add_subtask("Add type hints")
            goal.add_subtask("Update documentation")
            new_goals.append(goal)

        # Goal 2: Maintain zero known bugs
        if not any(g.title == "Zero known bugs" for g in self.active_goals):
            goal = Goal(
                title="Zero known bugs",
                description="Keep issue tracker clear of bug reports",
                priority=GoalPriority.HIGH,
                tags=['bugs', 'quality'],
            )
            goal.add_subtask("Monitor open bug issues")
            goal.add_subtask("Triage and fix bugs")
            goal.add_subtask("Prevent regressions")
            new_goals.append(goal)

        # Goal 3: Keep dependencies updated
        if not any(g.title == "Updated dependencies" for g in self.active_goals):
            goal = Goal(
                title="Updated dependencies",
                description="Keep all dependencies up to date and secure",
                priority=GoalPriority.MEDIUM,
                tags=['dependencies', 'security'],
            )
            goal.add_subtask("Monitor dependency updates")
            goal.add_subtask("Test compatibility")
            goal.add_subtask("Update regularly")
            new_goals.append(goal)

        # Add to active goals
        self.active_goals.extend(new_goals)

        if new_goals:
            logger.info(f"Generated {len(new_goals)} new proactive goals")

        return new_goals

    def get_active_goals(self) -> List[Goal]:
        """Get currently active goals"""
        return [g for g in self.active_goals if g.status != GoalStatus.COMPLETED]

    def should_approve_decision(self, decision: Decision) -> bool:
        """
        Determine if a decision should be auto-approved

        Args:
            decision: Decision to evaluate

        Returns:
            True if should be executed without human approval
        """
        # Never auto-approve if explicitly required
        if decision.requires_approval and not self.auto_approve:
            return False

        # Check confidence threshold
        if decision.confidence < self.min_confidence:
            return False

        # Check rate limiting
        # (Would need to implement rate tracking)

        return True
