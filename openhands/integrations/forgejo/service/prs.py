from __future__ import annotations

from openhands.integrations.forgejo.service.base import ForgejoMixinBase


class ForgejoPRsMixin(ForgejoMixinBase):
    """Pull request helpers for Forgejo."""

    async def get_pr_details(self, repository: str, pr_number: int) -> dict:  # type: ignore[override]
        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo, 'pulls', str(pr_number))
        response, _ = await self._make_request(url)
        return response

    async def is_pr_open(self, repository: str, pr_number: int) -> bool:  # type: ignore[override]
        pr_details = await self.get_pr_details(repository, pr_number)
        return (pr_details.get('state') or '').lower() == 'open'
