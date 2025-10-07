import asyncio
import time

from github import Github
from enterprise.integrations.github.github_view import (
    GithubInlinePRComment,
    GithubIssueComment,
    GithubPRComment,
)
from enterprise.integrations.solvability.data import load_classifier
from enterprise.integrations.solvability.models.report import SolvabilityReport
from enterprise.integrations.solvability.models.summary import SolvabilitySummary
from enterprise.integrations.types import ResolverViewInterface
from enterprise.integrations.utils import ENABLE_SOLVABILITY_ANALYSIS
from pydantic import ValidationError
from enterprise.server.config import get_config
from enterprise.storage.database import session_maker
from enterprise.storage.saas_settings_store import SaasSettingsStore

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.utils import create_registry_and_conversation_stats


def fetch_github_issue_context(
    full_repo_name: str,
    issue_number: int,
    user_token: str,
    max_comments: int = 10,
    max_comment_length: int = 500,
) -> str:
    """Fetch full GitHub issue/PR context including title, body, and comments.

    Args:
        full_repo_name: Full repository name in the format 'owner/repo'
        issue_number: The issue or PR number
        user_token: GitHub user access token
        max_comments: Maximum number of comments to fetch (default: 10)
        max_comment_length: Maximum length of each comment to include in the context (default: 500)

    Returns:
        A comprehensive string containing the issue/PR context
    """

    def _truncate_comment(comment_body: str) -> str:
        """Truncate comment body to a maximum length."""
        if len(comment_body) > max_comment_length:
            return comment_body[:max_comment_length] + '...'
        return comment_body

    with Github(user_token) as github_client:
        repo = github_client.get_repo(full_repo_name)

        # Get the issue/PR object
        issue = repo.get_issue(issue_number)

        # Build context string
        context_parts = []

        # Add title and body
        context_parts.append(f'Title: {issue.title}')
        if issue.body:
            context_parts.append(f'Description:\n{issue.body}')

        # Add labels if any
        if issue.labels:
            labels = [label.name for label in issue.labels]
            context_parts.append(f"Labels: {', '.join(labels)}")

        # Add recent comments (limit to avoid too much text)
        comments = list(issue.get_comments())
        if comments:
            context_parts.append('\nRecent Comments:')
            for comment in comments[-max_comments:]:
                context_parts.append(
                    f'- {comment.user.login}: {_truncate_comment(comment.body)}'
                )

        return '\n\n'.join(context_parts)


async def summarize_issue_solvability(
    resolver_view: ResolverViewInterface,
    user_token: str,
    timeout: float = 60.0 * 5,
) -> str:
    """Generate a solvability summary for an issue using the resolver view interface.

    Args:
        resolver_view: A resolver view interface instance (e.g., GithubIssue, GithubPRComment)
        user_token: GitHub user access token for API access
        timeout: Maximum time in seconds to wait for the result (default: 60.0)

    Returns:
        The solvability summary as a string

    Raises:
        ValueError: If LLM settings cannot be found for the user
        asyncio.TimeoutError: If the operation exceeds the specified timeout
    """
    if not ENABLE_SOLVABILITY_ANALYSIS:
        raise ValueError('Solvability report feature is disabled')

    if resolver_view.user_info.keycloak_user_id is None:
        raise ValueError(
            f'[Solvability] No user ID found for user {resolver_view.user_info.username}'
        )

    # Grab the user's information so we can load their LLM configuration
    store = SaasSettingsStore(
        user_id=resolver_view.user_info.keycloak_user_id,
        session_maker=session_maker,
        config=get_config(),
    )

    user_settings = await store.load()

    if user_settings is None:
        raise ValueError(
            f'[Solvability] No user settings found for user ID {resolver_view.user_info.user_id}'
        )

    # Check if solvability analysis is enabled for this user, exit early if
    # needed
    if not getattr(user_settings, 'enable_solvability_analysis', False):
        raise ValueError(
            f'Solvability analysis disabled for user {resolver_view.user_info.user_id}'
        )

    try:
        llm_config = LLMConfig(
            model=user_settings.llm_model,
            api_key=user_settings.llm_api_key.get_secret_value(),
            base_url=user_settings.llm_base_url,
        )
    except ValidationError as e:
        raise ValueError(
            f'[Solvability] Invalid LLM configuration for user {resolver_view.user_info.user_id}: {str(e)}'
        )

    # Fetch the full GitHub issue/PR context using the GitHub API
    start_time = time.time()
    issue_context = fetch_github_issue_context(
        resolver_view.full_repo_name, resolver_view.issue_number, user_token
    )
    logger.info(
        f'[Solvability] Grabbed issue context for {resolver_view.conversation_id}',
        extra={
            'conversation_id': resolver_view.conversation_id,
            'response_latency': time.time() - start_time,
            'full_repo_name': resolver_view.full_repo_name,
            'issue_number': resolver_view.issue_number,
        },
    )

    # For comment-based triggers, also include the specific comment that triggered the action
    if isinstance(
        resolver_view, (GithubIssueComment, GithubPRComment, GithubInlinePRComment)
    ):
        issue_context += f'\n\nTriggering Comment:\n{resolver_view.comment_body}'

    solvability_classifier = load_classifier('default-classifier')

    async with asyncio.timeout(timeout):
        solvability_report: SolvabilityReport = await call_sync_from_async(
            lambda: solvability_classifier.solvability_report(
                issue_context, llm_config=llm_config
            )
        )

        logger.info(
            f'[Solvability] Generated report for {resolver_view.conversation_id}',
            extra={
                'conversation_id': resolver_view.conversation_id,
                'report': solvability_report.model_dump(exclude=['issue']),
            },
        )

        llm_registry, _, _ = create_registry_and_conversation_stats(
            get_config(),
            resolver_view.conversation_id,
            resolver_view.user_info.keycloak_user_id,
            None,
        )

        solvability_summary = await call_sync_from_async(
            lambda: SolvabilitySummary.from_report(
                solvability_report, llm_config=llm_config
            )
        )
        logger.info(
            f'[Solvability] Generated summary for {resolver_view.conversation_id}',
            extra={
                'conversation_id': resolver_view.conversation_id,
                'summary': solvability_summary.model_dump(exclude=['content']),
            },
        )

        return solvability_summary.format_as_markdown()
