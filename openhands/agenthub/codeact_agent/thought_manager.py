"""Thought manager for tracking sequential thoughts and branches."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Thought:
    """A single thought in a sequential thinking process.

    Attributes:
        thought: The content of the thought.
        thought_number: The number of this thought in the sequence.
        total_thoughts: The estimated total number of thoughts needed.
        next_thought_needed: Whether another thought step is needed.
        is_revision: Whether this thought revises previous thinking.
        revises_thought: If is_revision is true, which thought number is being reconsidered.
        branch_from_thought: If branching, which thought number is the branching point.
        branch_id: Identifier for the current branch.
        needs_more_thoughts: If reaching end but realizing more thoughts needed.
    """

    thought: str
    thought_number: int
    total_thoughts: int
    next_thought_needed: bool
    is_revision: bool = False
    revises_thought: int = 0
    branch_from_thought: int = 0
    branch_id: str = ''
    needs_more_thoughts: bool = False


@dataclass
class ThoughtBranch:
    """A branch of thoughts in a sequential thinking process.

    Attributes:
        branch_id: Identifier for this branch.
        parent_branch_id: Identifier for the parent branch, if any.
        branch_from_thought: The thought number in the parent branch where this branch starts.
        thoughts: The list of thoughts in this branch.
    """

    branch_id: str
    parent_branch_id: str
    branch_from_thought: int
    thoughts: List[Thought] = field(default_factory=list)


class ThoughtManager:
    """Manager for tracking sequential thoughts and branches.

    This class stores and manages thoughts and thought branches for the sequential thinking tool.
    It provides methods to add thoughts, create branches, and retrieve thought history.
    """

    def __init__(self):
        """Initialize the thought manager."""
        self.main_branch_id = 'main'
        self.current_branch_id = self.main_branch_id
        self.branches: Dict[str, ThoughtBranch] = {
            self.main_branch_id: ThoughtBranch(
                branch_id=self.main_branch_id,
                parent_branch_id='',
                branch_from_thought=0,
            )
        }
        self.next_branch_id = 1

    def add_thought(self, thought: Thought) -> None:
        """Add a thought to the current branch.

        If the thought is a branch, create a new branch and add the thought to it.

        Args:
            thought: The thought to add.
        """
        # Handle branching
        if thought.branch_from_thought > 0 and thought.branch_id:
            # Use the provided branch_id if it exists, otherwise generate a new one
            branch_id = thought.branch_id
            if branch_id not in self.branches:
                self.branches[branch_id] = ThoughtBranch(
                    branch_id=branch_id,
                    parent_branch_id=self.current_branch_id,
                    branch_from_thought=thought.branch_from_thought,
                )
            self.current_branch_id = branch_id

        # Add the thought to the current branch
        self.branches[self.current_branch_id].thoughts.append(thought)

    def get_current_branch(self) -> ThoughtBranch:
        """Get the current branch.

        Returns:
            The current branch.
        """
        return self.branches[self.current_branch_id]

    def get_branch(self, branch_id: str) -> Optional[ThoughtBranch]:
        """Get a branch by ID.

        Args:
            branch_id: The ID of the branch to get.

        Returns:
            The branch, or None if it doesn't exist.
        """
        return self.branches.get(branch_id)

    def get_all_branches(self) -> List[ThoughtBranch]:
        """Get all branches.

        Returns:
            A list of all branches.
        """
        return list(self.branches.values())

    def get_thought_history(self, branch_id: Optional[str] = None) -> List[Thought]:
        """Get the thought history for a branch.

        Args:
            branch_id: The ID of the branch to get the history for. If None, use the current branch.

        Returns:
            The list of thoughts in the branch.
        """
        branch_id = branch_id or self.current_branch_id
        branch = self.branches.get(branch_id)
        if not branch:
            return []
        return branch.thoughts

    def get_latest_thought(self, branch_id: Optional[str] = None) -> Optional[Thought]:
        """Get the latest thought in a branch.

        Args:
            branch_id: The ID of the branch to get the latest thought for. If None, use the current branch.

        Returns:
            The latest thought, or None if the branch is empty.
        """
        thoughts = self.get_thought_history(branch_id)
        if not thoughts:
            return None
        return thoughts[-1]

    def generate_branch_id(self) -> str:
        """Generate a new branch ID.

        Returns:
            A new branch ID.
        """
        branch_id = f'branch_{self.next_branch_id}'
        self.next_branch_id += 1
        return branch_id

    def switch_branch(self, branch_id: str) -> bool:
        """Switch to a different branch.

        Args:
            branch_id: The ID of the branch to switch to.

        Returns:
            True if the switch was successful, False otherwise.
        """
        if branch_id not in self.branches:
            return False
        self.current_branch_id = branch_id
        return True

    def format_thought_history(self, branch_id: Optional[str] = None) -> str:
        """Format the thought history for a branch as a string.

        Args:
            branch_id: The ID of the branch to format the history for. If None, use the current branch.

        Returns:
            A formatted string representation of the thought history.
        """
        thoughts = self.get_thought_history(branch_id)
        if not thoughts:
            return 'No thoughts yet.'

        result = []
        for thought in thoughts:
            prefix = f'Thought {thought.thought_number}/{thought.total_thoughts}'

            if thought.is_revision and thought.revises_thought > 0:
                prefix += f' (revising thought {thought.revises_thought})'
            elif thought.branch_from_thought > 0 and thought.branch_id:
                prefix += f' (branch from thought {thought.branch_from_thought}, ID: {thought.branch_id})'

            result.append(f'{prefix}: {thought.thought}')

        return '\n\n'.join(result)
