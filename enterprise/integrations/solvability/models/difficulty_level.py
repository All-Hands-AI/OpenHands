from __future__ import annotations

from enum import Enum


class DifficultyLevel(Enum):
    """Enum representing the difficulty level based on solvability score."""

    EASY = ('EASY', 0.7, '🟢')
    MEDIUM = ('MEDIUM', 0.4, '🟡')
    HARD = ('HARD', 0.0, '🔴')

    def __init__(self, label: str, threshold: float, emoji: str):
        self.label = label
        self.threshold = threshold
        self.emoji = emoji

    @classmethod
    def from_score(cls, score: float) -> DifficultyLevel:
        """Get difficulty level from a solvability score.

        Returns the difficulty level with the highest threshold that is less than or equal to the given score.
        """
        # Sort enum values by threshold in descending order
        sorted_levels = sorted(cls, key=lambda x: x.threshold, reverse=True)

        # Find the first level where score meets the threshold
        for level in sorted_levels:
            if score >= level.threshold:
                return level

        # This should never happen if thresholds are set correctly,
        # but return the lowest threshold level as fallback
        return sorted_levels[-1]

    def format_display(self) -> str:
        """Format the difficulty level for display."""
        return f'{self.emoji} **Solvability: {self.label}**'
