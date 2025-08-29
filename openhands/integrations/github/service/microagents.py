import base64

from openhands.integrations.github.service.base import GitHubMixinBase
from openhands.integrations.service_types import (
    MicroagentContentResponse,
)


class GitHubMicroagentsMixin(GitHubMixinBase):
    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file."""
        return f'{self.BASE_URL}/repos/{repository}/contents/.cursorrules'

    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory."""
        return f'{self.BASE_URL}/repos/{repository}/contents/{microagents_path}'

    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        return (
            item['type'] == 'file'
            and item['name'].endswith('.md')
            and item['name'] != 'README.md'
        )

    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        return item['name']

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        return f'{microagents_path}/{item["name"]}'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request. Return None if no parameters needed."""
        return None

    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        """Fetch individual file content from GitHub repository.

        Args:
            repository: Repository name in format 'owner/repo'
            file_path: Path to the file within the repository

        Returns:
            MicroagentContentResponse with parsed content and triggers

        Raises:
            RuntimeError: If file cannot be fetched or doesn't exist
        """
        file_url = f'{self.BASE_URL}/repos/{repository}/contents/{file_path}'

        file_data, _ = await self._make_request(file_url)
        file_content = base64.b64decode(file_data['content']).decode('utf-8')

        # Parse the content to extract triggers from frontmatter
        return self._parse_microagent_content(file_content, file_path)
