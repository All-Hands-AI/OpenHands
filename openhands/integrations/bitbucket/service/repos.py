import re
from typing import Any

from openhands.integrations.bitbucket.service.base import BitBucketMixinBase
from openhands.integrations.service_types import Repository, SuggestedTask
from openhands.server.types import AppMode


class BitBucketReposMixin(BitBucketMixinBase):
    """
    Mixin for BitBucket repository-related operations
    """

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str, public: bool
    ) -> list[Repository]:
        """Search for repositories."""
        repositories = []

        if public:
            # Extract workspace and repo from URL
            # URL format: https://{domain}/{workspace}/{repo}/{additional_params}
            # Split by '/' and find workspace and repo parts
            url_parts = query.split('/')
            if len(url_parts) >= 5:  # https:, '', domain, workspace, repo
                workspace_slug = url_parts[3]
                repo_name = url_parts[4]

                repo = await self.get_repository_details_from_repo_name(
                    f'{workspace_slug}/{repo_name}'
                )
                repositories.append(repo)

            return repositories

        # Search for repos once workspace prefix exists
        if '/' in query:
            workspace_slug, repo_query = query.split('/', 1)
            return await self.get_paginated_repos(
                1, per_page, sort, workspace_slug, repo_query
            )

        all_installations = await self.get_installations()

        # Workspace prefix isn't complete. Search workspace names and repos underneath each workspace
        matching_workspace_slugs = [
            installation for installation in all_installations if query in installation
        ]
        for workspace_slug in matching_workspace_slugs:
            # Get repositories where query matches workspace name
            try:
                repos = await self.get_paginated_repos(
                    1, per_page, sort, workspace_slug
                )
                repositories.extend(repos)
            except Exception:
                continue

        for workspace_slug in all_installations:
            # Get repositories in all workspaces where query matches repo name
            try:
                repos = await self.get_paginated_repos(
                    1, per_page, sort, workspace_slug, query
                )
                repositories.extend(repos)
            except Exception:
                continue

        return repositories

    async def _get_user_workspaces(self) -> list[dict[str, Any]]:
        """Get all workspaces the user has access to"""
        url = f'{self.BASE_URL}/workspaces'
        data, _ = await self._make_request(url)
        return data.get('values', [])

    async def _fetch_paginated_data(
        self, url: str, params: dict, max_items: int
    ) -> list[dict]:
        """Fetch data with pagination support for Bitbucket API.

        Args:
            url: The API endpoint URL
            params: Query parameters for the request
            max_items: Maximum number of items to fetch

        Returns:
            List of data items from all pages
        """
        all_items: list[dict] = []
        current_url = url

        while current_url and len(all_items) < max_items:
            response, _ = await self._make_request(current_url, params)

            # Extract items from response
            page_items = response.get('values', [])
            if not page_items:  # No more items
                break

            all_items.extend(page_items)

            # Get the next page URL from the response
            current_url = response.get('next')

            # Clear params for subsequent requests since the next URL already contains all parameters
            params = {}

        return all_items[:max_items]  # Trim to max_items if needed

    async def get_installations(
        self, query: str | None = None, limit: int = 100
    ) -> list[str]:
        workspaces_url = f'{self.BASE_URL}/workspaces'
        params = {}
        if query:
            params['q'] = f'name~"{query}"'

        workspaces = await self._fetch_paginated_data(workspaces_url, params, limit)

        installations: list[str] = []
        for workspace in workspaces:
            installations.append(workspace['slug'])

        return installations

    async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ) -> list[Repository]:
        """Get paginated repositories for a specific workspace.

        Args:
            page: The page number to fetch
            per_page: The number of repositories per page
            sort: The sort field ('pushed', 'updated', 'created', 'full_name')
            installation_id: The workspace slug to fetch repositories from (as int, will be converted to string)

        Returns:
            A list of Repository objects
        """
        if not installation_id:
            return []

        # Convert installation_id to string for use as workspace_slug
        workspace_slug = installation_id
        workspace_repos_url = f'{self.BASE_URL}/repositories/{workspace_slug}'

        # Map sort parameter to Bitbucket API compatible values
        bitbucket_sort = sort
        if sort == 'pushed':
            # Bitbucket doesn't support 'pushed', use 'updated_on' instead
            bitbucket_sort = '-updated_on'  # Use negative prefix for descending order
        elif sort == 'updated':
            bitbucket_sort = '-updated_on'
        elif sort == 'created':
            bitbucket_sort = '-created_on'
        elif sort == 'full_name':
            bitbucket_sort = 'name'  # Bitbucket uses 'name' not 'full_name'
        else:
            # Default to most recently updated first
            bitbucket_sort = '-updated_on'

        params = {
            'pagelen': per_page,
            'page': page,
            'sort': bitbucket_sort,
        }

        if query:
            params['q'] = f'name~"{query}"'

        response, headers = await self._make_request(workspace_repos_url, params)

        # Extract repositories from the response
        repos = response.get('values', [])

        # Extract next URL from response
        next_link = response.get('next', '')

        # Format the link header in a way that the frontend can understand
        # The frontend expects a format like: <url>; rel="next"
        # where the URL contains a page parameter
        formatted_link_header = ''
        if next_link:
            # Extract the page number from the next URL if possible
            page_match = re.search(r'[?&]page=(\d+)', next_link)
            if page_match:
                next_page = page_match.group(1)
                # Format it in a way that extractNextPageFromLink in frontend can parse
                formatted_link_header = (
                    f'<{workspace_repos_url}?page={next_page}>; rel="next"'
                )
            else:
                # If we can't extract the page, just use the next URL as is
                formatted_link_header = f'<{next_link}>; rel="next"'

        repositories = [
            self._parse_repository(repo, link_header=formatted_link_header)
            for repo in repos
        ]

        return repositories

    async def get_all_repositories(
        self, sort: str, app_mode: AppMode
    ) -> list[Repository]:
        """Get repositories for the authenticated user using workspaces endpoint.

        This method gets all repositories (both public and private) that the user has access to
        by iterating through their workspaces and fetching repositories from each workspace.
        This approach is more comprehensive and efficient than the previous implementation
        that made separate calls for public and private repositories.
        """
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by Bitbucket API
        repositories: list[Repository] = []

        # Get user's workspaces with pagination
        workspaces_url = f'{self.BASE_URL}/workspaces'
        workspaces = await self._fetch_paginated_data(workspaces_url, {}, MAX_REPOS)

        for workspace in workspaces:
            workspace_slug = workspace.get('slug')
            if not workspace_slug:
                continue

            # Get repositories for this workspace with pagination
            workspace_repos_url = f'{self.BASE_URL}/repositories/{workspace_slug}'

            # Map sort parameter to Bitbucket API compatible values and ensure descending order
            # to show most recently changed repos at the top
            bitbucket_sort = sort
            if sort == 'pushed':
                # Bitbucket doesn't support 'pushed', use 'updated_on' instead
                bitbucket_sort = (
                    '-updated_on'  # Use negative prefix for descending order
                )
            elif sort == 'updated':
                bitbucket_sort = '-updated_on'
            elif sort == 'created':
                bitbucket_sort = '-created_on'
            elif sort == 'full_name':
                bitbucket_sort = 'name'  # Bitbucket uses 'name' not 'full_name'
            else:
                # Default to most recently updated first
                bitbucket_sort = '-updated_on'

            params = {
                'pagelen': PER_PAGE,
                'sort': bitbucket_sort,
            }

            # Fetch all repositories for this workspace with pagination
            workspace_repos = await self._fetch_paginated_data(
                workspace_repos_url, params, MAX_REPOS - len(repositories)
            )

            for repo in workspace_repos:
                repositories.append(self._parse_repository(repo))

                # Stop if we've reached the maximum number of repositories
                if len(repositories) >= MAX_REPOS:
                    break

            # Stop if we've reached the maximum number of repositories
            if len(repositories) >= MAX_REPOS:
                break

        return repositories

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories."""
        # TODO: implemented suggested tasks
        return []
