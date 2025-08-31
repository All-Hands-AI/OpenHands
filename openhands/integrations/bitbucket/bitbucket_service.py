import os

from openhands.integrations.bitbucket.service import (
    BitBucketBranchesMixin,
    BitBucketFeaturesMixin,
    BitBucketMixinBase,
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
    BitBucketMixinBase,
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

    @property
    def provider(self) -> str:
        return ProviderType.BITBUCKET.value


bitbucket_service_cls = os.environ.get(
    'OPENHANDS_BITBUCKET_SERVICE_CLS',
    'openhands.integrations.bitbucket.bitbucket_service.BitBucketService',
)
BitBucketServiceImpl = get_impl(BitBucketService, bitbucket_service_cls)
