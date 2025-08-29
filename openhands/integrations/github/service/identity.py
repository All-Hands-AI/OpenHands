from openhands.integrations.github.service.base import GitHubMixinBase
from openhands.integrations.service_types import User


class GitHubIdentityMixin(GitHubMixinBase):
    async def get_user(self) -> User:
        url = f'{self.BASE_URL}/user'
        response, _ = await self._make_request(url)

        return User(
            id=str(response.get('id', '')),
            login=response.get('login'),
            avatar_url=response.get('avatar_url'),
            company=response.get('company'),
            name=response.get('name'),
            email=response.get('email'),
        )

    async def verify_access(self) -> bool:
        """Verify if the token is valid by making a simple request."""
        url = f'{self.BASE_URL}'
        await self._make_request(url)
        return True
