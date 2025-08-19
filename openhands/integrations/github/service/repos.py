from datetime import datetime
from typing import cast

from openhands.integrations.github.service._base import GitHubMixinBase
from openhands.integrations.service_types import OwnerType, ProviderType, Repository


class GitHubReposMixin(GitHubMixinBase):
    async def _fetch_paginated_repos(
        self, url: str, params: dict, max_repos: int, extract_key: str | None = None
    ) -> list[dict]:
        repos: list[dict] = []
        page = 1

        while len(repos) < max_repos:
            page_params = {**params, 'page': str(page)}
            response, headers = await self._make_request(url, page_params)

            page_repos = response.get(extract_key, []) if extract_key else response
            if not page_repos:
                break

            repos.extend(page_repos)
            page += 1

            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

        return repos[:max_repos]

    def parse_pushed_at_date(self, repo: dict) -> datetime:
        ts = repo.get('pushed_at')
        return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ') if ts else datetime.min

    def _parse_repository(
        self, repo: dict, link_header: str | None = None
    ) -> Repository:
        return Repository(
            id=str(repo.get('id')),
            full_name=cast(str, repo.get('full_name') or ''),
            stargazers_count=repo.get('stargazers_count'),
            git_provider=ProviderType.GITHUB,
            is_public=not repo.get('private', True),
            owner_type=(
                OwnerType.ORGANIZATION
                if repo.get('owner', {}).get('type') == 'Organization'
                else OwnerType.USER
            ),
            link_header=link_header,
        )

    async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ):
        params = {'page': str(page), 'per_page': str(per_page)}
        if installation_id:
            url = f'{self.BASE_URL}/user/installations/{installation_id}/repositories'
            response, headers = await self._make_request(url, params)
            response = response.get('repositories', [])
        else:
            url = f'{self.BASE_URL}/user/repos'
            params['sort'] = sort
            response, headers = await self._make_request(url, params)

        next_link: str = headers.get('Link', '')
        return [
            self._parse_repository(repo, link_header=next_link) for repo in response
        ]

    async def get_all_repositories(
        self, sort: str, app_mode
    ):  # AppMode type avoided to prevent cycle
        from openhands.server.types import AppMode

        MAX_REPOS = 1000
        PER_PAGE = 100
        all_repos: list[dict] = []

        if app_mode == AppMode.SAAS:
            installation_ids = await self.get_installations()
            for installation_id in installation_ids:
                params = {'per_page': str(PER_PAGE)}
                url = (
                    f'{self.BASE_URL}/user/installations/{installation_id}/repositories'
                )
                installation_repos = await self._fetch_paginated_repos(
                    url, params, MAX_REPOS - len(all_repos), extract_key='repositories'
                )
                all_repos.extend(installation_repos)
                if len(all_repos) >= MAX_REPOS:
                    break

            if sort == 'pushed':
                all_repos.sort(key=self.parse_pushed_at_date, reverse=True)
        else:
            params = {'per_page': str(PER_PAGE), 'sort': sort}
            url = f'{self.BASE_URL}/user/repos'
            all_repos = await self._fetch_paginated_repos(url, params, MAX_REPOS)

        return [self._parse_repository(repo) for repo in all_repos]

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        url = f'{self.BASE_URL}/repos/{repository}'
        repo, _ = await self._make_request(url)
        return self._parse_repository(repo)

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str, public: bool
    ) -> list[Repository]:
        url = f'{self.BASE_URL}/search/repositories'
        params: dict = {
            'per_page': per_page,
            'sort': sort,
            'order': order,
        }

        if public:
            url_parts = query.split('/')
            if len(url_parts) < 4:
                return []
            org = url_parts[3]
            repo_name = url_parts[4]
            params['q'] = f'in:name {org}/{repo_name} is:public'

        if not public and '/' in query:
            org, repo_query = query.split('/', 1)
            query_with_user = f'org:{org} in:name {repo_query}'
            params['q'] = query_with_user
        elif not public:
            user = await self.get_user()
            params['q'] = f'in:name {query} user:{user.login}'

        response, _ = await self._make_request(url, params)
        repo_items = response.get('items', [])
        return [self._parse_repository(repo) for repo in repo_items]
