import base64
from urllib.parse import quote_plus
import os
import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import (
    AuthenticationError,
    GitService,
    ProviderType,
    Repository,
    UnknownException,
    User,
)
from openhands.utils.import_utils import get_impl


class AzureDevOpsService(GitService):
    token: SecretStr = SecretStr('')
    refresh = False

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
    ):        
        self.user_id = user_id
        self.external_token_manager = external_token_manager
        self.organization =  os.environ.get('AZURE_DEVOPS_ORG', '')
        self.project = os.environ.get('AZURE_DEVOPS_PROJECT', '')
        self.BASE_URL = f'https://dev.azure.com/{self.organization}/{self.project}'
        self.BASE_VSAEX_URL = f'https://vsaex.dev.azure.com/{self.organization}'

        if token:
            self.token = token


    async def load_settings(self) -> None:
        """
        Load settings from the SettingsStore
        """
        try:
            from openhands.server.shared import (
                SettingsStoreImpl,
                config,
                conversation_manager,
                sio,
            )
            
            if(self.organization and self.project):
                return
            settings_store = await SettingsStoreImpl.get_instance(config, None)
            settings = await settings_store.load()

            self.organization = settings.azure_devops_org or self.organization
            self.project = settings.azure_devops_project or self.project

            self.BASE_URL = f'https://dev.azure.com/{self.organization}/{self.project}'
            self.BASE_VSAEX_URL = f'https://vsaex.dev.azure.com/{self.organization}'

        except Exception as e:
            print(f'Error loading Azure DevOps settings: {e}')
            pass

    async def _get_azuredevops_headers(self, contentType = "application/json") -> dict:
        """
        Retrieve the Azure DevOps Token to construct the headers
        """
        if self.user_id and not self.token:
            self.token = await self.get_latest_token()

        # Azure DevOps uses Basic authentication with PAT
        # The username is ignored (empty string), and the password is the PAT
        # Create base64 encoded credentials (username:PAT)
        credentials = base64.b64encode(
            f':{self.token.get_secret_value()}'.encode()
        ).decode()

        return {
            'Authorization': f'Basic {credentials}',
            'Content-Type': contentType,
        }

    def _has_token_expired(self, status_code: int) -> bool:
        return status_code == 401

    async def get_latest_token(self) -> SecretStr | None:
        """
        Get the latest working token for the user
        """
        if self.external_token_manager:
            try:
                token_manager = get_impl('openhands.auth.token_manager', 'TokenManager')
                token = await token_manager.get_provider_token(
                    self.user_id, ProviderType.AZUREDEVOPS
                )
                if token:
                    self.token = token
                    return token
            except Exception as e:
                logger.error(f'Error getting Azure DevOps token: {e}')
                pass

        return self.token if self.token.get_secret_value() else None

    async def get_user(self) -> User:
        """
        Get the authenticated user's information from Azure DevOps
        """
        headers = await self._get_azuredevops_headers("application/json-patch+json")

        await self.load_settings()
        try:

            print(f"Azure DevOps base url: {self.BASE_URL}")
            print(f"Project: {self.project}")
            # Get the current user profile
            url = (
                f"{self.BASE_URL}/_apis/wit/workitems/$Task"
                f"?api-version=7.1-preview.3&validateOnly=true"
            )

            payload = [
                {
                    "op": "add",
                    "path": "/fields/System.Title",
                    "value": "Teste para identificar usuário do PAT"
                }
            ]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )

            if response.status_code == 401:
                raise UnknownException('Invalid Azure DevOps PAT')
            elif response.status_code != 200:
                raise UnknownException(
                    f'Failed to simulate Work Item creation: {response.status_code} {response.text}'
                )

            data = response.json()
            created_by = data.get("fields", {}).get("System.CreatedBy", {})

            user_id = hash(created_by.get("id", "")) % (2**31)

            return User(
                id=user_id,
                login=created_by.get("uniqueName", ""),
                avatar_url=created_by.get("imageUrl", ""),
                name=created_by.get("displayName", ""),
                email=created_by.get("uniqueName", ""),
                company=None,
            )
        except httpx.RequestError as e:            
            raise UnknownException(f'Request error: {str(e)}')
        except Exception as e:
            print(f'Error: {str(e)}')

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
    ) -> list[Repository]:
        """
        Search for repositories in Azure DevOps
        """
        await self.load_settings()
        if not self.organization:
            return []

        headers = await self._get_azuredevops_headers()

        try:

            url = f'{self.BASE_URL}/_apis/git/repositories?searchCriteria.searchText={quote_plus(query)}&api-version=7.0'

            # Search for repositories in the organization
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                )

            if response.status_code == 401:
                raise AuthenticationError('Invalid Azure DevOps credentials')
            elif response.status_code != 200:
                raise UnknownException(
                    f'Failed to search repositories: {response.status_code} {response.text}'
                )

            response_data = response.json()
            repos_data = response_data.get('value', [])

            repositories = []
            for repo in repos_data[:per_page]:
                # Convert string ID to integer by hashing it
                repo_id = hash(repo.get('id', '')) % (2**31)
                repositories.append(
                    Repository(
                        id=repo_id,
                        full_name=f"{self.organization}/{repo.get('name', '')}",
                        git_provider=ProviderType.AZUREDEVOPS,
                        stargazers_count=None,
                        pushed_at=None,
                        is_public=False,
                    )
                )

            return repositories
        except httpx.RequestError as e:
            raise UnknownException(f'Request error: {str(e)}')

    async def get_repositories(
        self,
        sort: str,
        installation_id: int | None,
    ) -> list[Repository]:
        """
        Get repositories for the authenticated user in Azure DevOps
        """
        await self.load_settings()        
        if not self.organization:
            return []

        headers = await self._get_azuredevops_headers()

        try:

            url = f'{self.BASE_URL}/_apis/git/repositories?api-version=7.0'            
            # Get all repositories in the organization
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                )

            if response.status_code == 401:
                raise AuthenticationError('Invalid Azure DevOps credentials')
            elif response.status_code != 200:
                raise UnknownException(
                    f'Failed to get repositories: {response.status_code} {response.text}'
                )

            response_data = response.json()
            repos_data = response_data.get('value', [])

            repositories = []
            for repo in repos_data:
                # Convert string ID to integer by hashing it
                repo_id = hash(repo.get('id', '')) % (2**31)
                repositories.append(
                    Repository(
                        id=repo_id,
                        full_name=f"{self.organization}/{repo.get('name', '')}",
                        git_provider=ProviderType.AZUREDEVOPS,
                        stargazers_count=None,
                        pushed_at=None,
                        is_public=False,
                    )
                )

            return repositories
        except httpx.RequestError as e:
            raise UnknownException(f'Request error: {str(e)}')

    async def get_repo_url(self, repository: str) -> str:
        """
        Get the URL of a repository in Azure DevOps
        """
        await self.load_settings()        
        if not self.organization:
            return ''

        # Extract repository name from full path (organization/project/repository)
        parts = repository.split('/')
        if len(parts) < 2:
            return ''

        repo_name = parts[-1]

        headers = await self._get_azuredevops_headers()

        try:
            # Get repository details
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{self.BASE_URL}/_apis/git/repositories/{repo_name}?api-version=7.0',
                    headers=headers,
                )

            if response.status_code == 200:
                repo_data = response.json()
                return repo_data.get('remoteUrl', '').replace(f'https://{self.organization}', f'https://{self.token.get_secret_value()}')
            else:
                return ''
        except httpx.RequestError:
            return ''        


class AzureDevOpsServiceImpl(AzureDevOpsService):
    """Implementation of the Azure DevOps service"""

    pass
