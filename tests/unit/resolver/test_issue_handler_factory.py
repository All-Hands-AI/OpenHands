import pytest
from pydantic import SecretStr

from openhands.core.config import LLMConfig
from openhands.integrations.provider import ProviderType
from openhands.resolver.interfaces.github import GithubIssueHandler, GithubPRHandler
from openhands.resolver.interfaces.gitlab import GitlabIssueHandler, GitlabPRHandler
from openhands.resolver.interfaces.issue_definitions import (
    ServiceContextIssue,
    ServiceContextPR,
)
from openhands.resolver.issue_handler_factory import IssueHandlerFactory


@pytest.fixture
def llm_config():
    return LLMConfig(
        model='test-model',
        api_key=SecretStr('test-key'),
    )


@pytest.fixture
def factory_params(llm_config):
    return {
        'owner': 'test-owner',
        'repo': 'test-repo',
        'token': 'test-token',
        'username': 'test-user',
        'base_domain': 'github.com',
        'llm_config': llm_config,
    }


test_cases = [
    # platform, issue_type, expected_context_type, expected_handler_type
    (ProviderType.GITHUB, 'issue', ServiceContextIssue, GithubIssueHandler),
    (ProviderType.GITHUB, 'pr', ServiceContextPR, GithubPRHandler),
    (ProviderType.GITLAB, 'issue', ServiceContextIssue, GitlabIssueHandler),
    (ProviderType.GITLAB, 'pr', ServiceContextPR, GitlabPRHandler),
]


@pytest.mark.parametrize(
    'platform,issue_type,expected_context_type,expected_handler_type', test_cases
)
def test_handler_creation(
    factory_params,
    platform: ProviderType,
    issue_type: str,
    expected_context_type: type,
    expected_handler_type: type,
):
    factory = IssueHandlerFactory(
        **factory_params, platform=platform, issue_type=issue_type
    )

    handler = factory.create()

    assert isinstance(handler, expected_context_type)
    assert isinstance(handler._strategy, expected_handler_type)


def test_invalid_issue_type(factory_params):
    factory = IssueHandlerFactory(
        **factory_params, platform=ProviderType.GITHUB, issue_type='invalid'
    )

    with pytest.raises(ValueError, match='Invalid issue type: invalid'):
        factory.create()
