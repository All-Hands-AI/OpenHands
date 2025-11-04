"""
GitHub Events Monitor

Monitors GitHub for events:
- Issues (opened, closed, commented)
- Pull Requests (opened, merged, commented)
- Mentions
- Releases
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Set

from openhands.autonomous.perception.base import (
    BaseMonitor,
    EventPriority,
    EventType,
    PerceptionEvent,
)

logger = logging.getLogger(__name__)


class GitHubMonitor(BaseMonitor):
    """
    Monitors GitHub repository for events

    Requires: GITHUB_TOKEN environment variable
    """

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        check_interval: int = 300,  # 5 minutes default (GitHub rate limits)
        bot_username: Optional[str] = None,
    ):
        """
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            check_interval: Check interval in seconds (respect rate limits!)
            bot_username: Bot's GitHub username (to detect mentions)
        """
        super().__init__(name="GitHubMonitor", check_interval=check_interval)

        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.bot_username = bot_username or "openhands"

        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set, GitHubMonitor will not function")

        # State tracking
        self.last_check_time = datetime.now() - timedelta(hours=1)  # Start 1 hour ago
        self.processed_issue_ids: Set[int] = set()
        self.processed_pr_ids: Set[int] = set()
        self.processed_comment_ids: Set[int] = set()

    async def check(self) -> List[PerceptionEvent]:
        """Check for GitHub events"""
        if not self.github_token:
            return []

        events = []

        # Check issues
        issue_events = await self._check_issues()
        events.extend(issue_events)

        # Check pull requests
        pr_events = await self._check_pull_requests()
        events.extend(pr_events)

        # Check mentions
        mention_events = await self._check_mentions()
        events.extend(mention_events)

        # Update last check time
        self.last_check_time = datetime.now()

        return events

    async def _github_request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        Make GitHub API request

        This is a placeholder - in a real implementation, you'd use aiohttp or similar.
        """
        # TODO: Implement actual GitHub API calls using aiohttp
        # For now, return None to indicate no implementation

        # Example implementation would look like:
        # import aiohttp
        # async with aiohttp.ClientSession() as session:
        #     headers = {
        #         'Authorization': f'token {self.github_token}',
        #         'Accept': 'application/vnd.github.v3+json',
        #     }
        #     url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/{endpoint}'
        #     async with session.get(url, headers=headers, params=params) as resp:
        #         if resp.status == 200:
        #             return await resp.json()
        #         else:
        #             logger.error(f"GitHub API error: {resp.status}")
        #             return None

        logger.debug(f"GitHub API placeholder called: {endpoint}")
        return None

    async def _check_issues(self) -> List[PerceptionEvent]:
        """Check for issue events"""
        events = []

        # Get recent issues
        # since = self.last_check_time.isoformat()
        # issues_data = await self._github_request('issues', {'since': since, 'state': 'all'})

        # Placeholder implementation
        issues_data = None

        if not issues_data:
            return events

        for issue_data in issues_data:
            issue_id = issue_data['number']

            # Skip if already processed
            if issue_id in self.processed_issue_ids:
                continue

            # Check issue state
            state = issue_data['state']
            created_at = datetime.fromisoformat(issue_data['created_at'].replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(issue_data['updated_at'].replace('Z', '+00:00'))

            # New issue
            if created_at > self.last_check_time:
                events.append(
                    PerceptionEvent(
                        event_type=EventType.GITHUB_ISSUE_OPENED,
                        priority=self._determine_issue_priority(issue_data),
                        timestamp=datetime.now(),
                        source=self.name,
                        data={
                            'issue_number': issue_id,
                            'title': issue_data['title'],
                            'author': issue_data['user']['login'],
                            'body': issue_data['body'],
                            'labels': [label['name'] for label in issue_data.get('labels', [])],
                            'url': issue_data['html_url'],
                        },
                    )
                )
                logger.info(f"New issue detected: #{issue_id} - {issue_data['title']}")

            # Closed issue
            elif state == 'closed' and updated_at > self.last_check_time:
                events.append(
                    PerceptionEvent(
                        event_type=EventType.GITHUB_ISSUE_CLOSED,
                        priority=EventPriority.LOW,
                        timestamp=datetime.now(),
                        source=self.name,
                        data={
                            'issue_number': issue_id,
                            'title': issue_data['title'],
                            'url': issue_data['html_url'],
                        },
                    )
                )
                logger.info(f"Issue closed: #{issue_id}")

            self.processed_issue_ids.add(issue_id)

        return events

    def _determine_issue_priority(self, issue_data: dict) -> EventPriority:
        """Determine priority of an issue"""
        labels = [label['name'].lower() for label in issue_data.get('labels', [])]
        title = issue_data['title'].lower()
        body = (issue_data.get('body') or '').lower()

        # Critical: Security, production issues
        if any(label in labels for label in ['security', 'critical', 'urgent', 'p0']):
            return EventPriority.CRITICAL

        # High: Bugs, blockers
        if any(label in labels for label in ['bug', 'blocker', 'p1']):
            return EventPriority.HIGH

        # High: Mentions of error, crash, broken
        if any(word in title or word in body for word in ['error', 'crash', 'broken', 'not working']):
            return EventPriority.HIGH

        # Medium: Features, enhancements
        if any(label in labels for label in ['enhancement', 'feature', 'p2']):
            return EventPriority.MEDIUM

        # Low: Documentation, questions
        if any(label in labels for label in ['documentation', 'question', 'good first issue']):
            return EventPriority.LOW

        return EventPriority.MEDIUM

    async def _check_pull_requests(self) -> List[PerceptionEvent]:
        """Check for pull request events"""
        events = []

        # Placeholder - similar to _check_issues
        # In real implementation, fetch PRs from GitHub API

        return events

    async def _check_mentions(self) -> List[PerceptionEvent]:
        """Check for mentions of the bot"""
        events = []

        # Placeholder - search for @bot_username in comments and issues
        # In real implementation, use GitHub search API

        return events
