"""
Tests for Consciousness Core (L2)
"""

import pytest

from openhands.autonomous.consciousness.core import ConsciousnessCore
from openhands.autonomous.consciousness.decision import Decision, DecisionType
from openhands.autonomous.consciousness.goal import Goal, GoalPriority, GoalStatus
from openhands.autonomous.perception.base import EventPriority, EventType


class TestConsciousnessCore:
    """Tests for ConsciousnessCore class"""

    def test_create_core(self):
        """Test creating consciousness core"""
        core = ConsciousnessCore(autonomy_level='medium', auto_approve=False)

        assert core.autonomy_level == 'medium'
        assert not core.auto_approve
        assert core.active_goals == []
        assert core.decisions == []

    def test_autonomy_levels(self):
        """Test different autonomy levels"""
        # Low autonomy
        core_low = ConsciousnessCore(autonomy_level='low')
        assert core_low.min_confidence == 0.8
        assert core_low.max_auto_decisions_per_hour == 5

        # Medium autonomy
        core_med = ConsciousnessCore(autonomy_level='medium')
        assert core_med.min_confidence == 0.6
        assert core_med.max_auto_decisions_per_hour == 20

        # High autonomy
        core_high = ConsciousnessCore(autonomy_level='high')
        assert core_high.min_confidence == 0.4
        assert core_high.max_auto_decisions_per_hour == 100

    @pytest.mark.asyncio
    async def test_process_test_failure(self, consciousness_core, sample_perception_event):
        """Test processing test failure event"""
        # Sample event is a test failure
        decision = await consciousness_core.process_event(sample_perception_event)

        assert decision is not None
        assert decision.decision_type == DecisionType.FIX_BUG
        assert decision.confidence > 0
        assert len(decision.trigger_events) == 1
        assert 'task' in decision.action_plan

    @pytest.mark.asyncio
    async def test_process_git_commit(self, consciousness_core, sample_git_commit_event):
        """Test processing git commit event"""
        decision = await consciousness_core.process_event(sample_git_commit_event)

        # May or may not generate decision depending on commit content
        # The test commit is a bug fix, so should generate test improvement decision
        if decision:
            assert decision.decision_type in [DecisionType.IMPROVE_TESTS, DecisionType.NO_ACTION]

    @pytest.mark.asyncio
    async def test_process_github_issue(self, consciousness_core, sample_issue_event):
        """Test processing GitHub issue event"""
        decision = await consciousness_core.process_event(sample_issue_event)

        # Should generate decision to respond
        assert decision is not None
        assert decision.decision_type == DecisionType.RESPOND_TO_ISSUE
        assert decision.action_plan['issue_number'] == 123

    @pytest.mark.asyncio
    async def test_generate_proactive_goals(self, consciousness_core):
        """Test generating proactive goals"""
        goals = await consciousness_core.generate_proactive_goals()

        # Should generate some goals
        assert len(goals) > 0

        # Check goal properties
        for goal in goals:
            assert isinstance(goal, Goal)
            assert goal.status == GoalStatus.PENDING
            assert len(goal.subtasks) > 0

        # Goals should be added to active goals
        assert len(consciousness_core.active_goals) == len(goals)

    @pytest.mark.asyncio
    async def test_proactive_goals_not_duplicated(self, consciousness_core):
        """Test that proactive goals are not duplicated"""
        goals1 = await consciousness_core.generate_proactive_goals()
        count1 = len(goals1)

        # Generate again - should not create duplicates
        goals2 = await consciousness_core.generate_proactive_goals()
        count2 = len(goals2)

        assert count2 == 0  # No new goals
        assert len(consciousness_core.active_goals) == count1

    def test_should_approve_decision(self, consciousness_core, sample_decision):
        """Test decision approval logic"""
        # High confidence, no explicit approval required
        sample_decision.confidence = 0.9
        sample_decision.requires_approval = False

        assert consciousness_core.should_approve_decision(sample_decision)

        # Low confidence
        sample_decision.confidence = 0.3
        assert not consciousness_core.should_approve_decision(sample_decision)

        # Explicitly requires approval
        sample_decision.confidence = 0.9
        sample_decision.requires_approval = True
        assert not consciousness_core.should_approve_decision(sample_decision)

        # Auto approve enabled
        consciousness_core.auto_approve = True
        assert consciousness_core.should_approve_decision(sample_decision)

    def test_get_active_goals(self, consciousness_core):
        """Test getting active goals"""
        # Create some goals
        goal1 = Goal(
            title="Test Goal 1",
            description="Description",
            priority=GoalPriority.HIGH,
        )
        goal2 = Goal(
            title="Test Goal 2",
            description="Description",
            priority=GoalPriority.MEDIUM,
            status=GoalStatus.COMPLETED,
        )

        consciousness_core.active_goals = [goal1, goal2]

        # Get active goals (should exclude completed)
        active = consciousness_core.get_active_goals()
        assert len(active) == 1
        assert active[0] == goal1


class TestDecision:
    """Tests for Decision class"""

    def test_create_decision(self, sample_perception_event):
        """Test creating a decision"""
        decision = Decision(
            decision_type=DecisionType.FIX_BUG,
            trigger_events=[sample_perception_event],
            reasoning="Tests are failing",
            confidence=0.8,
        )

        assert decision.decision_type == DecisionType.FIX_BUG
        assert len(decision.trigger_events) == 1
        assert decision.confidence == 0.8
        assert not decision.executed
        assert decision.id.startswith('dec_')

    def test_decision_to_dict(self, sample_decision):
        """Test serializing decision to dict"""
        data = sample_decision.to_dict()

        assert data['decision_type'] == 'fix_bug'
        assert data['confidence'] == 0.8
        assert 'timestamp' in data
        assert 'action_plan' in data


class TestGoal:
    """Tests for Goal class"""

    def test_create_goal(self):
        """Test creating a goal"""
        goal = Goal(
            title="Improve code quality",
            description="Refactor and optimize codebase",
            priority=GoalPriority.MEDIUM,
        )

        assert goal.title == "Improve code quality"
        assert goal.priority == GoalPriority.MEDIUM
        assert goal.status == GoalStatus.PENDING
        assert goal.progress == 0.0
        assert goal.id.startswith('goal_')

    def test_goal_lifecycle(self):
        """Test goal lifecycle"""
        goal = Goal(
            title="Test Goal",
            description="Test",
            priority=GoalPriority.HIGH,
        )

        # Start goal
        goal.mark_started()
        assert goal.status == GoalStatus.IN_PROGRESS
        assert goal.started_at is not None

        # Complete goal
        goal.mark_completed(success=True)
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completed_at is not None
        assert goal.progress == 1.0

    def test_goal_subtasks(self):
        """Test goal subtasks"""
        goal = Goal(
            title="Test Goal",
            description="Test",
            priority=GoalPriority.HIGH,
        )

        # Add subtasks
        goal.add_subtask("Task 1")
        goal.add_subtask("Task 2")
        goal.add_subtask("Task 3")

        assert len(goal.subtasks) == 3
        assert goal.progress == 0.0

        # Complete subtasks
        goal.complete_subtask("Task 1")
        assert goal.progress == pytest.approx(1/3)

        goal.complete_subtask("Task 2")
        assert goal.progress == pytest.approx(2/3)

        goal.complete_subtask("Task 3")
        assert goal.progress == 1.0

    def test_goal_to_dict(self):
        """Test serializing goal to dict"""
        goal = Goal(
            title="Test Goal",
            description="Test",
            priority=GoalPriority.HIGH,
        )

        data = goal.to_dict()

        assert data['title'] == "Test Goal"
        assert data['priority'] == GoalPriority.HIGH.value
        assert data['status'] == GoalStatus.PENDING.value
        assert 'created_at' in data
