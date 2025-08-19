import os

from openhands.integrations.github.service import (
    GitHubService as _AssembledGitHubService,
)
from openhands.utils.import_utils import get_impl


# Re-export the assembled service under the same name and path to preserve public API
class GitHubService(_AssembledGitHubService):
    pass


github_service_cls = os.environ.get(
    'OPENHANDS_GITHUB_SERVICE_CLS',
    'openhands.integrations.github.github_service.GitHubService',
)
GithubServiceImpl = get_impl(GitHubService, github_service_cls)
