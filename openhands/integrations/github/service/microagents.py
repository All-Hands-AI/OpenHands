import base64

from openhands.integrations.github.service._base import GitHubMixinBase
from openhands.integrations.service_types import (
    MicroagentContentResponse,
)


class GitHubMicroagentsMixin(GitHubMixinBase):
    async def _get_cursorrules_url(self, repository: str) -> str:
        return f'{self.BASE_URL}/repos/{repository}/contents/.cursorrules'

    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        return f'{self.BASE_URL}/repos/{repository}/contents/{microagents_path}'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        return None

    def _is_valid_microagent_file(self, item: dict) -> bool:
        return (
            item['type'] == 'file'
            and item['name'].endswith('.md')
            and item['name'] != 'README.md'
        )

    def _get_file_name_from_item(self, item: dict) -> str:
        return item['name']

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        return f'{microagents_path}/{item["name"]}'

    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        file_url = f'{self.BASE_URL}/repos/{repository}/contents/{file_path}'
        file_data, _ = await self._make_request(file_url)
        file_content = base64.b64decode(file_data['content']).decode('utf-8')
        return self._parse_microagent_content(file_content, file_path)
