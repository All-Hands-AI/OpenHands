from __future__ import annotations

from openhands.integrations.forgejo.service.base import ForgejoMixinBase
from openhands.integrations.service_types import RequestMethod, UnknownException
from openhands.core.logger import openhands_logger as logger


class ForgejoPRsMixin(ForgejoMixinBase):
    """Pull request helpers for Forgejo."""

    async def create_pull_request(self, data: dict[str, object] | None = None) -> dict:
        payload = data or {}

        owner = payload.pop('owner', None) or self.user_id or ''
        repo = payload.pop('repo', None)
        if not repo:
            raise ValueError('Repository name must be provided to create a pull request')

        url = self._build_repo_api_url(owner, repo, 'pulls')
        response, _ = await self._make_request(
            url,
            payload,
            method=RequestMethod.POST,
        )

        if not isinstance(response, dict):
            raise UnknownException('Unexpected response creating Forgejo pull request')

        if 'number' not in response and 'index' in response:
            response['number'] = response['index']

        return response

    async def request_reviewers(
        self, repository: str, pr_number: int, reviewers: list[str]
    ) -> None:
        if not reviewers:
            return

        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo, 'pulls', str(pr_number), 'requested_reviewers')

        try:
            await self._make_request(
                url,
                {'reviewers': reviewers},
                method=RequestMethod.POST,
            )
        except Exception as exc:  # pragma: no cover - log and continue
            logger.warning(
                'Failed to request Forgejo reviewers %s for %s/%s PR #%s: %s',
                reviewers,
                owner,
                repo,
                pr_number,
                exc,
            )

    async def get_pr_details(self, repository: str, pr_number: int) -> dict:  # type: ignore[override]
        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo, 'pulls', str(pr_number))
        response, _ = await self._make_request(url)
        return response

    async def is_pr_open(self, repository: str, pr_number: int) -> bool:  # type: ignore[override]
        pr_details = await self.get_pr_details(repository, pr_number)
        return (pr_details.get('state') or '').lower() == 'open'
