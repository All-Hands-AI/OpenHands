import os

from typing import Literal

from pydantic import SecretStr

from openhands.integrations.bitbucket.service import (
    BitBucketBranchesMixin,
    BitBucketFeaturesMixin,
    BitBucketPRsMixin,
    BitBucketReposMixin,
)
from openhands.integrations.service_types import (
    GitService,
    InstallationsService,
    ProviderType,
)
from openhands.utils.import_utils import get_impl


class BitBucketService(
    BitBucketReposMixin,
    BitBucketBranchesMixin,
    BitBucketPRsMixin,
    BitBucketFeaturesMixin,
    GitService,
    InstallationsService,
):
    """Default implementation of GitService for Bitbucket integration.

    This is an extension point in OpenHands that allows applications to customize Bitbucket
    integration behavior. Applications can substitute their own implementation by:
    1. Creating a class that inherits from GitService
    2. Implementing all required methods
    3. Setting server_config.bitbucket_service_class to the fully qualified name of the class

    The class is instantiated via get_impl() in openhands.server.shared.py.
    """

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_domain: str | None = None,
        bitbucket_mode: Literal['cloud', 'server'] = 'cloud',
    ) -> None:
        self.user_id = user_id
        self.external_token_manager = external_token_manager
        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token
        self.base_domain = base_domain or 'bitbucket.org'
        self.bitbucket_mode = bitbucket_mode

        if self.bitbucket_mode not in {'cloud', 'server'}:
            raise ValueError(
                f'Unsupported Bitbucket mode: {self.bitbucket_mode}'
            )

        if token:
            self.token = token
            token_value = token.get_secret_value()
            if ':' in token_value:
                self.user_id = self.user_id or token_value.split(':', 1)[0]

        if self.bitbucket_mode == 'server':
            self.BASE_URL = f'https://{self.base_domain}/rest/api/1.0'
        else:
            self.BASE_URL = f'https://api.{self.base_domain}/2.0'

    @property
    def provider(self) -> str:
        return ProviderType.BITBUCKET.value


bitbucket_service_cls = os.environ.get(
    'OPENHANDS_BITBUCKET_SERVICE_CLS',
    'openhands.integrations.bitbucket.bitbucket_service.BitBucketService',
)
BitBucketServiceImpl = get_impl(BitBucketService, bitbucket_service_cls)
