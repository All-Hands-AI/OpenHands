from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from openhands.core.logger import openhands_logger as logger
from openhands.microagent.microagent import BaseMicroagent
from openhands.microagent.types import MicroagentContentResponse, MicroagentResponse


class MicroagentParseError(ValueError):
    """Raised when there is an error parsing a microagent file."""

    pass


class MicroagentManagementClient(ABC):
    """Interface for managing microagents in git repositories."""

    @property
    @abstractmethod
    def provider(self) -> str:
        """Get the provider name."""
        ...

    @abstractmethod
    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: Any = None,
    ) -> tuple[Any, dict]:
        """Make a request to the provider's API."""
        ...

    @abstractmethod
    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file."""
        ...

    @abstractmethod
    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory."""
        ...

    @abstractmethod
    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request. Return None if no parameters needed."""
        ...

    @abstractmethod
    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        ...

    @abstractmethod
    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        ...

    @abstractmethod
    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        ...

    def _determine_microagents_path(self, repository_name: str) -> str:
        """Determine the microagents directory path based on repository name."""
        actual_repo_name = repository_name.split('/')[-1]

        # Check for special repository names that use a different structure
        if actual_repo_name == '.openhands' or actual_repo_name == 'openhands-config':
            # For repository name ".openhands", scan "microagents" folder
            return 'microagents'
        else:
            # Default behavior: look for .openhands/microagents directory
            return '.openhands/microagents'

    def _create_microagent_response(
        self, file_name: str, path: str
    ) -> MicroagentResponse:
        """Create a microagent response from basic file information."""
        # Extract name without extension
        name = file_name.replace('.md', '').replace('.cursorrules', 'cursorrules')

        return MicroagentResponse(
            name=name,
            path=path,
            created_at=datetime.now(),
        )

    def _parse_microagent_content(
        self, content: str, file_path: str
    ) -> MicroagentContentResponse:
        """Parse microagent content and extract triggers using BaseMicroagent.load.

        Args:
            content: Raw microagent file content
            file_path: Path to the file (used for microagent loading)

        Returns:
            MicroagentContentResponse with parsed content and triggers

        Raises:
            MicroagentParseError: If the microagent file cannot be parsed
        """
        try:
            # Use BaseMicroagent.load to properly parse the content
            # Create a temporary path object for the file
            temp_path = Path(file_path)

            # Load the microagent using the existing infrastructure
            microagent = BaseMicroagent.load(path=temp_path, file_content=content)

            # Extract triggers from the microagent's metadata
            triggers = microagent.metadata.triggers

            # Return the MicroagentContentResponse
            return MicroagentContentResponse(
                content=microagent.content,
                path=file_path,
                triggers=triggers,
                git_provider=self.provider,
            )

        except Exception as e:
            logger.error(f'Error parsing microagent content for {file_path}: {str(e)}')
            raise MicroagentParseError(
                f'Failed to parse microagent file {file_path}: {str(e)}'
            )

    async def _fetch_cursorrules_content(self, repository: str) -> Any | None:
        """Fetch .cursorrules file content from the repository via API.

        Args:
            repository: Repository name in format specific to the provider

        Returns:
            Raw API response content if .cursorrules file exists, None otherwise
        """
        cursorrules_url = await self._get_cursorrules_url(repository)
        cursorrules_response, _ = await self._make_request(cursorrules_url)
        return cursorrules_response

    async def _check_cursorrules_file(
        self, repository: str
    ) -> MicroagentResponse | None:
        """Check for .cursorrules file in the repository and return microagent response if found.

        Args:
            repository: Repository name in format specific to the provider

        Returns:
            MicroagentResponse for .cursorrules file if found, None otherwise
        """
        try:
            cursorrules_content = await self._fetch_cursorrules_content(repository)
            if cursorrules_content:
                return self._create_microagent_response('.cursorrules', '.cursorrules')
        except Exception as e:
            # Handle ResourceNotFoundError or similar exceptions
            if 'not found' in str(e).lower() or 'ResourceNotFoundError' in str(type(e)):
                logger.debug(f'No .cursorrules file found in {repository}')
            else:
                logger.warning(f'Error checking .cursorrules file in {repository}: {e}')

        return None

    async def _process_microagents_directory(
        self, repository: str, microagents_path: str
    ) -> list[MicroagentResponse]:
        """Process microagents directory and return list of microagent responses.

        Args:
            repository: Repository name in format specific to the provider
            microagents_path: Path to the microagents directory

        Returns:
            List of MicroagentResponse objects found in the directory
        """
        microagents = []

        try:
            directory_url = await self._get_microagents_directory_url(
                repository, microagents_path
            )
            directory_params = self._get_microagents_directory_params(microagents_path)
            response, _ = await self._make_request(directory_url, directory_params)

            # Handle different response structures
            items = response
            if isinstance(response, dict) and 'values' in response:
                # Bitbucket format
                items = response['values']
            elif isinstance(response, dict) and 'nodes' in response:
                # GraphQL format (if used)
                items = response['nodes']

            for item in items:
                if self._is_valid_microagent_file(item):
                    try:
                        file_name = self._get_file_name_from_item(item)
                        file_path = self._get_file_path_from_item(
                            item, microagents_path
                        )
                        microagents.append(
                            self._create_microagent_response(file_name, file_path)
                        )
                    except Exception as e:
                        logger.warning(
                            f'Error processing microagent {item.get("name", "unknown")}: {str(e)}'
                        )
        except Exception as e:
            # Handle ResourceNotFoundError or similar exceptions
            if 'not found' in str(e).lower() or 'ResourceNotFoundError' in str(type(e)):
                logger.info(
                    f'No microagents directory found in {repository} at {microagents_path}'
                )
            else:
                logger.warning(f'Error fetching microagents directory: {str(e)}')

        return microagents

    async def get_microagents(self, repository: str) -> list[MicroagentResponse]:
        """Generic implementation of get_microagents that works across all providers.

        Args:
            repository: Repository name in format specific to the provider

        Returns:
            List of microagents found in the repository (without content for performance)
        """
        microagents_path = self._determine_microagents_path(repository)
        microagents = []

        # Step 1: Check for .cursorrules file
        cursorrules_microagent = await self._check_cursorrules_file(repository)
        if cursorrules_microagent:
            microagents.append(cursorrules_microagent)

        # Step 2: Check for microagents directory and process .md files
        directory_microagents = await self._process_microagents_directory(
            repository, microagents_path
        )
        microagents.extend(directory_microagents)

        return microagents

    @abstractmethod
    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        """Get content of a specific microagent file

        Returns:
            MicroagentContentResponse with parsed content and triggers
        """
        ...
