from openhands.integrations.github.service._base import GitHubMixinBase


class GitHubInstallationsMixin(GitHubMixinBase):
    async def get_installations(self) -> list[str]:
        url = f'{self.BASE_URL}/user/installations'
        response, _ = await self._make_request(url)
        installations = response.get('installations', [])
        return [str(i['id']) for i in installations]
