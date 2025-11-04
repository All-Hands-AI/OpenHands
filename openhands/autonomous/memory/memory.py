"""
Memory System - Stores and learns from experiences
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from openhands.autonomous.executor.task import ExecutionTask, TaskStatus
from openhands.autonomous.memory.experience import Experience, ExperienceType

logger = logging.getLogger(__name__)


class MemorySystem:
    """
    L4: Learning & Memory System

    Stores experiences, identifies patterns, and generates knowledge.
    """

    def __init__(self, db_path: str = "memory/system.db"):
        """
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(f"Memory system initialized at {self.db_path}")

    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Experiences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY,
                experience_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                trigger TEXT,
                context TEXT,
                action_taken TEXT,
                reasoning TEXT,
                success INTEGER,
                outcome_description TEXT,
                artifacts TEXT,
                lessons_learned TEXT,
                confidence REAL,
                reusability_score REAL,
                tags TEXT,
                related_experiences TEXT
            )
        ''')

        # Patterns table (learned patterns)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                pattern_type TEXT,
                description TEXT,
                success_rate REAL,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                pattern_data TEXT
            )
        ''')

        # Microagents table (generated knowledge)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS microagents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                content TEXT,
                created_at TEXT,
                source_experiences TEXT,
                effectiveness_score REAL
            )
        ''')

        conn.commit()
        conn.close()

    async def record_experience(self, task: ExecutionTask) -> Experience:
        """
        Record an experience from a completed task

        Args:
            task: Completed execution task

        Returns:
            Created experience
        """
        # Determine experience type from decision type
        type_map = {
            'fix_bug': ExperienceType.BUG_FIX,
            'add_feature': ExperienceType.FEATURE_ADDITION,
            'refactor_code': ExperienceType.REFACTORING,
            'improve_tests': ExperienceType.TEST_IMPROVEMENT,
            'update_docs': ExperienceType.DOCUMENTATION,
            'respond_to_issue': ExperienceType.ISSUE_RESPONSE,
            'update_dependencies': ExperienceType.DEPENDENCY_UPDATE,
            'fix_security_issue': ExperienceType.SECURITY_FIX,
        }

        exp_type = type_map.get(
            task.decision.decision_type.value,
            ExperienceType.BUG_FIX
        )

        # Create experience
        experience = Experience(
            experience_type=exp_type,
            timestamp=datetime.now(),
            trigger=f"{task.decision.decision_type.value} decision",
            context={
                'decision_reasoning': task.decision.reasoning,
                'action_plan': task.decision.action_plan,
            },
            action_taken=task.decision.action_plan.get('task', 'unknown'),
            reasoning=task.decision.reasoning,
            success=task.status == TaskStatus.COMPLETED,
            outcome_description=task.output or task.error or "No output",
            artifacts=task.artifacts,
            confidence=task.decision.confidence,
        )

        # Analyze for lessons
        await self._extract_lessons(experience, task)

        # Calculate reusability
        experience.calculate_reusability()

        # Store in database
        self._store_experience(experience)

        logger.info(f"Recorded experience {experience.id}: {exp_type.value} (success: {experience.success})")

        return experience

    async def _extract_lessons(self, experience: Experience, task: ExecutionTask):
        """Extract lessons learned from an experience"""
        if experience.success:
            # Successful execution
            experience.add_lesson(f"Successfully handled {experience.experience_type.value}")

            # Check if faster than expected
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                if duration < 60:
                    experience.add_lesson("Task completed quickly, pattern is efficient")

        else:
            # Failed execution
            experience.add_lesson(f"Failed to handle {experience.experience_type.value}")

            # Analyze error
            if task.error:
                if "timeout" in task.error.lower():
                    experience.add_lesson("Task timed out, may need more time or different approach")
                elif "permission" in task.error.lower():
                    experience.add_lesson("Permission issue, may need different privileges")

    def _store_experience(self, experience: Experience):
        """Store experience in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO experiences VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            experience.id,
            experience.experience_type.value,
            experience.timestamp.isoformat(),
            experience.trigger,
            json.dumps(experience.context),
            experience.action_taken,
            experience.reasoning,
            1 if experience.success else 0,
            experience.outcome_description,
            json.dumps(experience.artifacts),
            json.dumps(experience.lessons_learned),
            experience.confidence,
            experience.reusability_score,
            json.dumps(experience.tags),
            json.dumps(experience.related_experiences),
        ))

        conn.commit()
        conn.close()

    def get_experiences(
        self,
        experience_type: Optional[ExperienceType] = None,
        success_only: bool = False,
        limit: int = 100,
    ) -> List[Experience]:
        """
        Retrieve experiences from memory

        Args:
            experience_type: Filter by type
            success_only: Only successful experiences
            limit: Max number to return

        Returns:
            List of experiences
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        query = "SELECT * FROM experiences WHERE 1=1"
        params = []

        if experience_type:
            query += " AND experience_type = ?"
            params.append(experience_type.value)

        if success_only:
            query += " AND success = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        experiences = []
        for row in rows:
            exp = Experience(
                id=row[0],
                experience_type=ExperienceType(row[1]),
                timestamp=datetime.fromisoformat(row[2]),
                trigger=row[3],
                context=json.loads(row[4]) if row[4] else {},
                action_taken=row[5],
                reasoning=row[6],
                success=bool(row[7]),
                outcome_description=row[8],
                artifacts=json.loads(row[9]) if row[9] else [],
                lessons_learned=json.loads(row[10]) if row[10] else [],
                confidence=row[11],
                reusability_score=row[12],
                tags=json.loads(row[13]) if row[13] else [],
                related_experiences=json.loads(row[14]) if row[14] else [],
            )
            experiences.append(exp)

        return experiences

    async def identify_patterns(self) -> List[dict]:
        """
        Identify patterns from experiences

        Analyzes experiences to find recurring successful patterns.
        """
        patterns = []

        # Get all successful experiences
        experiences = self.get_experiences(success_only=True)

        # Group by type
        by_type: dict[ExperienceType, List[Experience]] = {}
        for exp in experiences:
            if exp.experience_type not in by_type:
                by_type[exp.experience_type] = []
            by_type[exp.experience_type].append(exp)

        # Analyze each type
        for exp_type, exps in by_type.items():
            if len(exps) >= 3:  # Need at least 3 to identify pattern
                pattern = {
                    'type': exp_type.value,
                    'count': len(exps),
                    'success_rate': len([e for e in exps if e.success]) / len(exps),
                    'common_lessons': self._extract_common_lessons(exps),
                    'avg_confidence': sum(e.confidence for e in exps) / len(exps),
                }
                patterns.append(pattern)

        logger.info(f"Identified {len(patterns)} patterns from {len(experiences)} experiences")

        return patterns

    def _extract_common_lessons(self, experiences: List[Experience]) -> List[str]:
        """Extract lessons that appear in multiple experiences"""
        lesson_counts: dict[str, int] = {}

        for exp in experiences:
            for lesson in exp.lessons_learned:
                lesson_counts[lesson] = lesson_counts.get(lesson, 0) + 1

        # Return lessons that appear in at least 30% of experiences
        threshold = len(experiences) * 0.3
        common = [lesson for lesson, count in lesson_counts.items() if count >= threshold]

        return common

    async def generate_microagent(self, pattern: dict) -> Optional[str]:
        """
        Generate a microagent from a learned pattern

        Args:
            pattern: Pattern dict from identify_patterns()

        Returns:
            Microagent content (markdown), or None
        """
        if pattern['success_rate'] < 0.7:
            logger.info(f"Pattern {pattern['type']} success rate too low: {pattern['success_rate']}")
            return None

        # Generate microagent content
        content = f"""# {pattern['type'].replace('_', ' ').title()}

## Pattern Description
This is an automatically generated microagent based on learned experiences.

**Type:** {pattern['type']}
**Success Rate:** {pattern['success_rate']:.1%}
**Based on:** {pattern['count']} successful experiences
**Confidence:** {pattern['avg_confidence']:.2f}

## Lessons Learned

"""

        for lesson in pattern['common_lessons']:
            content += f"- {lesson}\n"

        content += """

## Recommendations

When handling this type of task:
1. Follow the patterns that have worked before
2. Apply the lessons learned above
3. Monitor for similar issues in the future

---
*Generated by OpenHands Autonomous Learning System*
"""

        # Store microagent
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO microagents (name, description, content, created_at, source_experiences, effectiveness_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            pattern['type'],
            f"Auto-generated from {pattern['count']} experiences",
            content,
            datetime.now().isoformat(),
            json.dumps([]),  # Could track specific experience IDs
            pattern['success_rate'],
        ))

        conn.commit()
        conn.close()

        logger.info(f"Generated microagent for pattern: {pattern['type']}")

        return content

    def get_statistics(self) -> dict:
        """Get memory statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM experiences")
        total_experiences = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM experiences WHERE success = 1")
        successful_experiences = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM patterns")
        total_patterns = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM microagents")
        total_microagents = cursor.fetchone()[0]

        conn.close()

        return {
            'total_experiences': total_experiences,
            'successful_experiences': successful_experiences,
            'success_rate': successful_experiences / total_experiences if total_experiences > 0 else 0,
            'total_patterns': total_patterns,
            'total_microagents': total_microagents,
        }
