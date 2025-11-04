"""
Git Repository Monitor

Monitors git repository for changes:
- New commits
- Branch creation/deletion
- Tag creation
- File changes
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from openhands.autonomous.perception.base import (
    BaseMonitor,
    EventPriority,
    EventType,
    PerceptionEvent,
)

logger = logging.getLogger(__name__)


class GitMonitor(BaseMonitor):
    """
    Monitors git repository for changes

    Detects:
    - New commits on tracked branches
    - New branches
    - Deleted branches
    - New tags
    """

    def __init__(
        self,
        repo_path: str,
        check_interval: int = 60,
        branches_to_watch: Optional[List[str]] = None,
    ):
        """
        Args:
            repo_path: Path to git repository
            check_interval: Check interval in seconds
            branches_to_watch: Branches to watch (None = all branches)
        """
        super().__init__(name="GitMonitor", check_interval=check_interval)

        self.repo_path = Path(repo_path)
        self.branches_to_watch = branches_to_watch or []

        # State tracking
        self.last_commits: dict[str, str] = {}  # branch -> commit_hash
        self.known_branches: Set[str] = set()
        self.known_tags: Set[str] = set()

        # Initialize state
        self._initialize_state()

    def _initialize_state(self):
        """Initialize tracking state from current git state"""
        try:
            # Get all branches
            result = self._git_command(['branch', '-r'])
            if result:
                self.known_branches = set(
                    line.strip().replace('origin/', '')
                    for line in result.split('\n')
                    if line.strip() and '->' not in line
                )

            # Get latest commit for each branch
            for branch in self.known_branches:
                commit = self._get_latest_commit(branch)
                if commit:
                    self.last_commits[branch] = commit

            # Get all tags
            result = self._git_command(['tag'])
            if result:
                self.known_tags = set(line.strip() for line in result.split('\n') if line.strip())

            logger.info(
                f"GitMonitor initialized: {len(self.known_branches)} branches, "
                f"{len(self.known_tags)} tags"
            )
        except Exception as e:
            logger.error(f"Failed to initialize GitMonitor: {e}")

    def _git_command(self, args: List[str]) -> Optional[str]:
        """Run git command and return output"""
        try:
            result = subprocess.run(
                ['git', '-C', str(self.repo_path)] + args,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"Git command failed: {' '.join(args)}\n{result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timeout: {' '.join(args)}")
            return None
        except Exception as e:
            logger.error(f"Git command error: {e}")
            return None

    def _get_latest_commit(self, branch: str) -> Optional[str]:
        """Get latest commit hash for a branch"""
        result = self._git_command(['rev-parse', f'origin/{branch}'])
        return result if result else None

    def _get_commit_info(self, commit_hash: str) -> dict:
        """Get detailed info about a commit"""
        # Get commit message
        message = self._git_command(['log', '-1', '--format=%s', commit_hash]) or ""

        # Get author
        author = self._git_command(['log', '-1', '--format=%an', commit_hash]) or ""

        # Get changed files
        files_output = self._git_command(['diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash]) or ""
        files = [f for f in files_output.split('\n') if f]

        return {
            'hash': commit_hash,
            'message': message,
            'author': author,
            'files_changed': files,
            'file_count': len(files),
        }

    async def check(self) -> List[PerceptionEvent]:
        """Check for git changes"""
        events = []

        # Fetch latest from remote
        await asyncio.to_thread(self._git_command, ['fetch', '--all', '--prune'])

        # Check for new/deleted branches
        branch_events = await self._check_branches()
        events.extend(branch_events)

        # Check for new commits
        commit_events = await self._check_commits()
        events.extend(commit_events)

        # Check for new tags
        tag_events = await self._check_tags()
        events.extend(tag_events)

        return events

    async def _check_branches(self) -> List[PerceptionEvent]:
        """Check for branch changes"""
        events = []

        # Get current branches
        result = await asyncio.to_thread(self._git_command, ['branch', '-r'])
        if not result:
            return events

        current_branches = set(
            line.strip().replace('origin/', '')
            for line in result.split('\n')
            if line.strip() and '->' not in line
        )

        # New branches
        new_branches = current_branches - self.known_branches
        for branch in new_branches:
            events.append(
                PerceptionEvent(
                    event_type=EventType.GIT_BRANCH_CREATED,
                    priority=EventPriority.MEDIUM,
                    timestamp=datetime.now(),
                    source=self.name,
                    data={'branch': branch},
                )
            )
            logger.info(f"New branch detected: {branch}")

        # Deleted branches
        deleted_branches = self.known_branches - current_branches
        for branch in deleted_branches:
            events.append(
                PerceptionEvent(
                    event_type=EventType.GIT_BRANCH_DELETED,
                    priority=EventPriority.LOW,
                    timestamp=datetime.now(),
                    source=self.name,
                    data={'branch': branch},
                )
            )
            logger.info(f"Branch deleted: {branch}")

        # Update known branches
        self.known_branches = current_branches

        return events

    async def _check_commits(self) -> List[PerceptionEvent]:
        """Check for new commits"""
        events = []

        # Determine which branches to check
        branches = self.branches_to_watch if self.branches_to_watch else self.known_branches

        for branch in branches:
            # Get latest commit
            latest = await asyncio.to_thread(self._get_latest_commit, branch)
            if not latest:
                continue

            # Check if this is a new commit
            if branch in self.last_commits and self.last_commits[branch] != latest:
                # Get commit info
                commit_info = await asyncio.to_thread(self._get_commit_info, latest)

                # Determine priority based on content
                priority = self._determine_commit_priority(commit_info)

                events.append(
                    PerceptionEvent(
                        event_type=EventType.GIT_COMMIT,
                        priority=priority,
                        timestamp=datetime.now(),
                        source=self.name,
                        data={
                            'branch': branch,
                            'commit': commit_info,
                            'previous_commit': self.last_commits.get(branch),
                        },
                    )
                )
                logger.info(f"New commit on {branch}: {commit_info['message'][:50]}")

            # Update last commit
            self.last_commits[branch] = latest

        return events

    def _determine_commit_priority(self, commit_info: dict) -> EventPriority:
        """Determine priority of a commit based on its content"""
        message = commit_info['message'].lower()
        files = commit_info['files_changed']

        # Critical: Security fixes, hotfixes
        if any(word in message for word in ['security', 'hotfix', 'critical', 'urgent']):
            return EventPriority.CRITICAL

        # High: Bug fixes, important features
        if any(word in message for word in ['fix', 'bug', 'error', 'crash']):
            return EventPriority.HIGH

        # High: Changes to important files
        important_files = ['requirements.txt', 'package.json', 'Dockerfile', '.github/workflows']
        if any(any(important in f for important in important_files) for f in files):
            return EventPriority.HIGH

        # Medium: Features, refactoring
        if any(word in message for word in ['feat', 'feature', 'add', 'refactor']):
            return EventPriority.MEDIUM

        # Low: Docs, tests, chores
        if any(word in message for word in ['doc', 'test', 'chore', 'style']):
            return EventPriority.LOW

        return EventPriority.MEDIUM

    async def _check_tags(self) -> List[PerceptionEvent]:
        """Check for new tags"""
        events = []

        # Get current tags
        result = await asyncio.to_thread(self._git_command, ['tag'])
        if not result:
            return events

        current_tags = set(line.strip() for line in result.split('\n') if line.strip())

        # New tags
        new_tags = current_tags - self.known_tags
        for tag in new_tags:
            events.append(
                PerceptionEvent(
                    event_type=EventType.GIT_TAG_CREATED,
                    priority=EventPriority.HIGH,  # Tags usually mean releases
                    timestamp=datetime.now(),
                    source=self.name,
                    data={'tag': tag},
                )
            )
            logger.info(f"New tag detected: {tag}")

        # Update known tags
        self.known_tags = current_tags

        return events
