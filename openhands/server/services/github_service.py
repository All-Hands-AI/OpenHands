from fastapi.responses import JSONResponse
from github import Github
from github.GithubException import GithubException, UnknownObjectException, BadCredentialsException

from openhands.server.shared import server_config
from openhands.utils.async_utils import call_sync_from_async


class GitHubService:
    def __init__(self, token: str):
        self.token = token
        self.github = Github(token)

    def _has_token_expired(self, exception: GithubException):
        return isinstance(exception, BadCredentialsException)

    async def _refresh_token(self):
        pass

    async def _fetch_data(self, operation, *args, **kwargs):
        try:
            result = await call_sync_from_async(operation, *args, **kwargs)
            return JSONResponse(content=result, status_code=200)
        except BadCredentialsException as e:
            if server_config.app_mode == 'SAAS':
                await self._refresh_token()
                try:
                    result = await call_sync_from_async(operation, *args, **kwargs)
                    return JSONResponse(content=result, status_code=200)
                except GithubException as e:
                    return JSONResponse(
                        content={'error': str(e.data.get('message', str(e)))},
                        status_code=e.status
                    )
            return JSONResponse(
                content={'error': str(e.data.get('message', str(e)))},
                status_code=e.status
            )
        except UnknownObjectException as e:
            return JSONResponse(
                content={'error': 'Resource not found'},
                status_code=404
            )
        except GithubException as e:
            return JSONResponse(
                content={'error': str(e.data.get('message', str(e)))},
                status_code=e.status
            )
        except Exception as e:
            return JSONResponse(
                content={'error': str(e)},
                status_code=500
            )

    async def get_user(self):
        return await self._fetch_data(self.github.get_user().raw_data)

    async def get_repositories(
        self, page: int, per_page: int, sort: str, installation_id: int | None
    ):
        if installation_id:
            # Note: PyGithub doesn't directly support installation-specific repos
            # We'll need to implement this separately if needed
            raise NotImplementedError("Installation-specific repositories not supported yet")
        else:
            def get_repos():
                user = self.github.get_user()
                repos = user.get_repos(sort=sort)
                return [repo.raw_data for repo in repos.get_page(page-1)]
            return await self._fetch_data(get_repos)

    async def get_installation_ids(self):
        # Note: PyGithub doesn't directly support installations
        # We'll need to implement this separately if needed
        raise NotImplementedError("Installation IDs not supported yet")

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str
    ):
        def search():
            repos = self.github.search_repositories(
                query=query,
                sort=sort,
                order=order
            )
            return [repo.raw_data for repo in repos[:per_page]]
        return await self._fetch_data(search)

    async def fetch_response(self, method: str, *args, **kwargs):
        return await getattr(self, method)(*args, **kwargs)
