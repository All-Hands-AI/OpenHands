"""
Tests for Memory System (L4)
"""

import sqlite3
from datetime import datetime

import pytest

from openhands.autonomous.consciousness.decision import Decision, DecisionType
from openhands.autonomous.executor.task import ExecutionTask, TaskStatus
from openhands.autonomous.memory.experience import Experience, ExperienceType
from openhands.autonomous.memory.memory import MemorySystem
from openhands.autonomous.perception.base import EventPriority, EventType, PerceptionEvent


class TestExperience:
    """Tests for Experience class"""

    def test_create_experience(self):
        """Test creating an experience"""
        experience = Experience(
            experience_type=ExperienceType.BUG_FIX,
            timestamp=datetime.now(),
            trigger="test_failed",
            context={'test': 'value'},
            action_taken="Fixed the bug",
            reasoning="Bug was causing crash",
            success=True,
            outcome_description="Bug fixed successfully",
            confidence=0.8,
        )

        assert experience.experience_type == ExperienceType.BUG_FIX
        assert experience.success
        assert experience.confidence == 0.8
        assert experience.id.startswith('exp_')

    def test_add_lesson(self, sample_experience):
        """Test adding lessons to experience"""
        sample_experience.add_lesson("Always check input validation")
        sample_experience.add_lesson("Write regression tests")

        assert len(sample_experience.lessons_learned) == 2

    def test_calculate_reusability(self, sample_experience):
        """Test calculating reusability score"""
        # Add lessons
        sample_experience.add_lesson("Lesson 1")
        sample_experience.add_lesson("Lesson 2")

        # Calculate
        score = sample_experience.calculate_reusability()

        assert 0.0 <= score <= 1.0
        assert score > 0  # Should be non-zero for successful experience

        # Failed experience should have lower score
        failed_exp = Experience(
            experience_type=ExperienceType.BUG_FIX,
            timestamp=datetime.now(),
            trigger="test",
            context={},
            action_taken="Tried to fix",
            reasoning="Reason",
            success=False,
            outcome_description="Failed",
            confidence=0.5,
        )

        failed_score = failed_exp.calculate_reusability()
        assert failed_score < score

    def test_experience_serialization(self, sample_experience):
        """Test experience serialization"""
        # To dict
        data = sample_experience.to_dict()

        assert data['experience_type'] == ExperienceType.BUG_FIX.value
        assert data['success'] is True
        assert 'timestamp' in data

        # From dict
        restored = Experience.from_dict(data)

        assert restored.experience_type == sample_experience.experience_type
        assert restored.success == sample_experience.success
        assert restored.confidence == sample_experience.confidence


class TestMemorySystem:
    """Tests for MemorySystem class"""

    def test_create_memory_system(self, temp_db):
        """Test creating memory system"""
        memory = MemorySystem(db_path=str(temp_db))

        assert memory.db_path.exists()

        # Check tables exist
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert 'experiences' in tables
        assert 'patterns' in tables
        assert 'microagents' in tables

        conn.close()

    @pytest.mark.asyncio
    async def test_record_experience(self, memory_system, sample_decision):
        """Test recording an experience"""
        # Create a completed task
        task = ExecutionTask(decision=sample_decision)
        task.mark_started()
        task.mark_completed(output="Task completed successfully")

        # Record experience
        experience = await memory_system.record_experience(task)

        assert isinstance(experience, Experience)
        assert experience.success
        assert len(experience.lessons_learned) > 0

        # Verify stored in database
        experiences = memory_system.get_experiences(limit=10)
        assert len(experiences) == 1
        assert experiences[0].id == experience.id

    @pytest.mark.asyncio
    async def test_record_failed_experience(self, memory_system, sample_decision):
        """Test recording a failed experience"""
        # Create a failed task
        task = ExecutionTask(decision=sample_decision)
        task.mark_started()
        task.mark_failed("Something went wrong")

        # Record experience
        experience = await memory_system.record_experience(task)

        assert not experience.success
        assert "Failed" in experience.lessons_learned[0]

    def test_get_experiences(self, memory_system, sample_experience):
        """Test retrieving experiences"""
        # Store some experiences
        memory_system._store_experience(sample_experience)

        # Get all
        experiences = memory_system.get_experiences()
        assert len(experiences) == 1

        # Get by type
        experiences = memory_system.get_experiences(
            experience_type=ExperienceType.BUG_FIX
        )
        assert len(experiences) == 1

        # Get only successful
        experiences = memory_system.get_experiences(success_only=True)
        assert len(experiences) == 1

        # Get with limit
        experiences = memory_system.get_experiences(limit=0)
        assert len(experiences) == 0

    def test_get_experiences_by_type(self, memory_system):
        """Test filtering experiences by type"""
        # Create different types
        exp1 = Experience(
            experience_type=ExperienceType.BUG_FIX,
            timestamp=datetime.now(),
            trigger="test",
            context={},
            action_taken="action",
            reasoning="reason",
            success=True,
            outcome_description="outcome",
        )

        exp2 = Experience(
            experience_type=ExperienceType.REFACTORING,
            timestamp=datetime.now(),
            trigger="test",
            context={},
            action_taken="action",
            reasoning="reason",
            success=True,
            outcome_description="outcome",
        )

        memory_system._store_experience(exp1)
        memory_system._store_experience(exp2)

        # Filter by type
        bug_fixes = memory_system.get_experiences(experience_type=ExperienceType.BUG_FIX)
        assert len(bug_fixes) == 1

        refactorings = memory_system.get_experiences(
            experience_type=ExperienceType.REFACTORING
        )
        assert len(refactorings) == 1

    @pytest.mark.asyncio
    async def test_identify_patterns(self, memory_system):
        """Test identifying patterns from experiences"""
        # Create multiple similar experiences
        for i in range(5):
            exp = Experience(
                experience_type=ExperienceType.BUG_FIX,
                timestamp=datetime.now(),
                trigger="test_failed",
                context={},
                action_taken=f"Fixed bug {i}",
                reasoning="Bug fix",
                success=True,
                outcome_description="Success",
                confidence=0.8,
            )
            exp.add_lesson("Always check null values")
            memory_system._store_experience(exp)

        # Identify patterns
        patterns = await memory_system.identify_patterns()

        # Should find pattern for bug fixes
        assert len(patterns) > 0

        bug_fix_pattern = next(
            (p for p in patterns if p['type'] == 'bug_fix'), None
        )
        assert bug_fix_pattern is not None
        assert bug_fix_pattern['count'] == 5
        assert bug_fix_pattern['success_rate'] == 1.0
        assert 'Always check null values' in bug_fix_pattern['common_lessons']

    @pytest.mark.asyncio
    async def test_generate_microagent(self, memory_system):
        """Test generating a microagent from a pattern"""
        pattern = {
            'type': 'bug_fix',
            'count': 10,
            'success_rate': 0.9,
            'common_lessons': [
                'Validate inputs',
                'Write tests',
            ],
            'avg_confidence': 0.8,
        }

        # Generate microagent
        content = await memory_system.generate_microagent(pattern)

        assert content is not None
        assert 'Bug Fix' in content
        assert 'Validate inputs' in content
        assert '90.0%' in content  # Success rate

    @pytest.mark.asyncio
    async def test_skip_low_success_pattern(self, memory_system):
        """Test that low success patterns don't generate microagents"""
        pattern = {
            'type': 'test_type',
            'count': 10,
            'success_rate': 0.5,  # Too low
            'common_lessons': [],
            'avg_confidence': 0.6,
        }

        content = await memory_system.generate_microagent(pattern)
        assert content is None

    def test_get_statistics(self, memory_system):
        """Test getting memory statistics"""
        # Initially empty
        stats = memory_system.get_statistics()
        assert stats['total_experiences'] == 0

        # Add some experiences
        exp1 = Experience(
            experience_type=ExperienceType.BUG_FIX,
            timestamp=datetime.now(),
            trigger="test",
            context={},
            action_taken="action",
            reasoning="reason",
            success=True,
            outcome_description="outcome",
        )

        exp2 = Experience(
            experience_type=ExperienceType.BUG_FIX,
            timestamp=datetime.now(),
            trigger="test",
            context={},
            action_taken="action",
            reasoning="reason",
            success=False,
            outcome_description="outcome",
        )

        memory_system._store_experience(exp1)
        memory_system._store_experience(exp2)

        stats = memory_system.get_statistics()
        assert stats['total_experiences'] == 2
        assert stats['successful_experiences'] == 1
        assert stats['success_rate'] == 0.5

    def test_extract_common_lessons(self, memory_system):
        """Test extracting common lessons"""
        experiences = []

        # Create experiences with overlapping lessons
        for i in range(10):
            exp = Experience(
                experience_type=ExperienceType.BUG_FIX,
                timestamp=datetime.now(),
                trigger="test",
                context={},
                action_taken="action",
                reasoning="reason",
                success=True,
                outcome_description="outcome",
            )

            # Common lesson in all
            exp.add_lesson("Always validate inputs")

            # Less common lesson
            if i % 2 == 0:
                exp.add_lesson("Check edge cases")

            experiences.append(exp)

        # Extract common lessons (threshold 30%)
        common = memory_system._extract_common_lessons(experiences)

        assert "Always validate inputs" in common  # 100% frequency
        assert "Check edge cases" in common  # 50% frequency

    @pytest.mark.asyncio
    async def test_full_learning_cycle(self, memory_system, sample_decision):
        """Test full learning cycle: experience -> pattern -> microagent"""
        # Record multiple similar experiences
        for i in range(5):
            task = ExecutionTask(decision=sample_decision)
            task.mark_started()
            task.mark_completed(output=f"Success {i}")

            await memory_system.record_experience(task)

        # Identify patterns
        patterns = await memory_system.identify_patterns()
        assert len(patterns) > 0

        # Generate microagent
        for pattern in patterns:
            if pattern['success_rate'] >= 0.7:
                content = await memory_system.generate_microagent(pattern)
                if content:
                    assert 'OpenHands Autonomous Learning System' in content
                    break
