import os
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    AuthenticationError,
    Branch,
    GitService,
    MicroagentContentResponse,
    MicroagentResponse,
    OwnerType,
    PaginatedBranchesResponse,
    ProviderType,
    Repository,
    SuggestedTask,
    UnknownException,
    User,
)
from openhands.server.types import AppMode
from openhands.utils.import_utils import get_impl


class ForgejoService(GitService):
    # Default to Codeberg, can be overridden
    DEFAULT_BASE_URL = 'https://codeberg.org/api/v1'
    DEFAULT_DOMAIN = 'codeberg.org'
    token: SecretStr = SecretStr('')
    refresh = False

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_domain: str | None = None,
        base_url: str | None = None,
    ):
        self.user_id = user_id
        self.external_token_manager = external_token_manager

        if token:
            self.token = token

        # Resolve base URL with priority: explicit parameter, provider token host, env var, default
        env_base_url = os.environ.get('FORGEJO_BASE_URL')
        self.base_url = self._resolve_base_url(base_url, base_domain, env_base_url)
        parsed = urlparse(self.base_url)
        self.base_domain = parsed.netloc or self.DEFAULT_DOMAIN

    def _resolve_base_url(
        self,
        explicit_base_url: str | None,
        base_domain: str | None,
        env_base_url: str | None,
    ) -> str:
        for candidate in (explicit_base_url, base_domain, env_base_url, self.DEFAULT_BASE_URL):
            if not candidate:
                continue

            normalized = candidate.strip().rstrip('/')
            if not normalized:
                continue

            if normalized.startswith('http://') or normalized.startswith('https://'):
                url = normalized
            else:
                url = f'https://{normalized}'

            if '/api/' in url:
                return url

            return f'{url}/api/v1'

        return self.DEFAULT_BASE_URL

    async def _get_forgejo_headers(self) -> dict:
        """
        Retrieve the Forgejo Token to construct the headers
        """
        if self.user_id and not self.token:
            self.token = await self.get_latest_token()

        return {
            'Authorization': f'token {self.token.get_secret_value()}',
            'Accept': 'application/json',
        }

    def _has_token_expired(self, status_code: int) -> bool:
        return status_code == 401

    async def get_latest_token(self) -> SecretStr | None:
        return self.token

    async def _fetch_data(
        self, url: str, params: dict | None = None
    ) -> tuple[Any, dict]:
        try:
            async with httpx.AsyncClient() as client:
                forgejo_headers = await self._get_forgejo_headers()
                response = await client.get(url, headers=forgejo_headers, params=params)
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    forgejo_headers = await self._get_forgejo_headers()
                    response = await client.get(
                        url, headers=forgejo_headers, params=params
                    )

                response.raise_for_status()
                headers: dict[str, str] = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']
                if 'X-Total-Count' in response.headers:
                    headers['X-Total-Count'] = response.headers['X-Total-Count']

                return response.json(), headers

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError('Invalid Forgejo token')
            raise UnknownException(f'Unknown error: {e}')

        except httpx.HTTPError as e:
            raise UnknownException(f'HTTP error: {e}')

    async def get_user(self) -> User:
        url = f'{self.base_url}/user'
        response, _ = await self._fetch_data(url)

        return User(
            id=str(response.get('id', '')),
            avatar_url=response.get('avatar_url', ''),
            name=response.get('full_name'),
            email=response.get('email'),
            company=response.get('organization'),
            login=response.get('username', ''),
        )

    def _parse_repository(
        self, repo: dict, link_header: str | None = None
    ) -> Repository:
        owner = repo.get('owner', {}) or {}
        owner_type = (
            OwnerType.ORGANIZATION
            if owner.get('type', '').lower() == 'organization'
            else OwnerType.USER
        )

        return Repository(
            id=str(repo.get('id', '')),
            full_name=repo.get('full_name', ''),
            stargazers_count=repo.get('stars_count'),
            git_provider=ProviderType.FORGEJO,
            is_public=not repo.get('private', False),
            link_header=link_header,
            pushed_at=repo.get('updated_at') or repo.get('pushed_at'),
            owner_type=owner_type,
            main_branch=repo.get('default_branch'),
        )

    def _split_repo(self, repository: str) -> tuple[str, str]:
        repo_path = repository.strip()
        if repo_path.startswith('http://') or repo_path.startswith('https://'):
            parsed = urlparse(repo_path)
            repo_path = parsed.path.lstrip('/')

        parts = [part for part in repo_path.split('/') if part]
        if len(parts) < 2:
            raise ValueError(f'Invalid repository format: {repository}')

        return parts[0], parts[1]

    def _build_repo_api_url(self, owner: str, repo: str, *segments: str) -> str:
        base = f'{self.base_url}/repos/{owner}/{repo}'
        if segments:
            base += '/' + '/'.join(segments)
        return base

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
        public: bool,
    ) -> list[Repository]:
        url = f'{self.base_url}/repos/search'
        params = {
            'q': query,
            'limit': per_page,
            'sort': sort,
            'order': order,
            'mode': 'source',  # Only return repositories that are not forks
        }

        response, _ = await self._fetch_data(url, params)
        repos = response.get('data', [])
        if public:
            repos = [repo for repo in repos if not repo.get('private', False)]
        return [self._parse_repository(repo) for repo in repos]

    async def get_all_repositories(
        self, sort: str, app_mode: AppMode
    ) -> list[Repository]:
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by Forgejo API
        all_repos: list[dict] = []
        page = 1
        last_headers: dict[str, str] | None = None

        url = f'{self.base_url}/user/repos'
        # Map GitHub's sort values to Forgejo's sort values
        sort_map = {
            'pushed': 'updated',
            'updated': 'updated',
            'created': 'created',
            'full_name': 'name',
        }
        forgejo_sort = sort_map.get(sort, 'updated')

        while len(all_repos) < MAX_REPOS:
            params = {
                'page': str(page),
                'limit': str(PER_PAGE),
                'sort': forgejo_sort,
            }
            response, headers = await self._fetch_data(url, params)
            last_headers = headers

            if not response:  # No more repositories
                break

            all_repos.extend(response)
            page += 1

            # Check if we've reached the last page
            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

        # Trim to MAX_REPOS if needed and convert to Repository objects
        all_repos = all_repos[:MAX_REPOS]
        link_header = last_headers.get('Link') if all_repos and last_headers else None

        return [self._parse_repository(repo, link_header=link_header) for repo in all_repos]

    async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ) -> list[Repository]:
        _ = installation_id  # Forgejo does not use installations
        url = f'{self.base_url}/user/repos'
        sort_map = {
            'pushed': 'updated',
            'updated': 'updated',
            'created': 'created',
            'full_name': 'name',
        }
        params = {
            'page': str(page),
            'limit': str(per_page),
            'sort': sort_map.get(sort, 'updated'),
        }

        response, headers = await self._fetch_data(url, params)
        repos = response or []

        if query:
            lowered = query.lower()
            repos = [
                repo
                for repo in repos
                if lowered in (repo.get('full_name') or '').lower()
            ]

        link_header = headers.get('Link')
        return [self._parse_repository(repo, link_header=link_header) for repo in repos]

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo)
        response, headers = await self._fetch_data(url)
        link_header = headers.get('Link')
        return self._parse_repository(response, link_header=link_header)

    async def get_branches(self, repository: str) -> list[Branch]:
        branches: list[Branch] = []
        page = 1
        per_page = 100

        while True:
            paginated = await self.get_paginated_branches(repository, page, per_page)
            branches.extend(paginated.branches)
            if not paginated.has_next_page:
                break
            page += 1

        return branches

    async def get_paginated_branches(
        self, repository: str, page: int = 1, per_page: int = 30
    ) -> PaginatedBranchesResponse:
        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo, 'branches')
        params = {
            'page': str(page),
            'limit': str(per_page),
        }

        response, headers = await self._fetch_data(url, params)
        branch_items = response if isinstance(response, list) else []

        branches = []
        for branch in branch_items:
            commit_info = branch.get('commit') or {}
            commit_sha = (
                commit_info.get('id')
                or commit_info.get('sha')
                or commit_info.get('commit', {}).get('sha')
            )
            branches.append(
                Branch(
                    name=branch.get('name', ''),
                    commit_sha=commit_sha or '',
                    protected=branch.get('protected', False),
                    last_push_date=None,
                )
            )

        link_header = headers.get('Link', '')
        total_count_header = headers.get('X-Total-Count')
        total_count = int(total_count_header) if total_count_header else None
        has_next_page = 'rel="next"' in link_header

        return PaginatedBranchesResponse(
            branches=branches,
            has_next_page=has_next_page,
            current_page=page,
            per_page=per_page,
            total_count=total_count,
        )

    async def search_branches(
        self, repository: str, query: str, per_page: int = 30
    ) -> list[Branch]:
        all_branches = await self.get_branches(repository)
        lowered = query.lower()
        return [
            branch
            for branch in all_branches
            if lowered in branch.name.lower()
        ][:per_page]

    async def get_microagents(self, repository: str) -> list[MicroagentResponse]:
        _ = repository
        return []

    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        _ = repository
        return MicroagentContentResponse(
            content='',
            path=file_path,
            triggers=[],
            git_provider=ProviderType.FORGEJO.value,
        )

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        return []

    async def get_pr_details(self, repository: str, pr_number: int) -> dict:
        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo, 'pulls', str(pr_number))
        response, _ = await self._fetch_data(url)
        return response

    async def is_pr_open(self, repository: str, pr_number: int) -> bool:
        pr_details = await self.get_pr_details(repository, pr_number)
        return pr_details.get('state', '').lower() == 'open'


forgejo_service_cls = os.environ.get(
    'OPENHANDS_FORGEJO_SERVICE_CLS',
    'openhands.integrations.forgejo.forgejo_service.ForgejoService',
)
ForgejoServiceImpl = get_impl(ForgejoService, forgejo_service_cls)
