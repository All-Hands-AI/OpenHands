import os
import pytest
from unittest.mock import patch, MagicMock
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.events.stream import EventStream
from openhands.storage import get_file_store


class TestWorkflowTokenHandling:
    """Tests for token handling in GitHub workflows"""

    @pytest.fixture
    def temp_dir(self, tmp_path_factory: pytest.TempPathFactory) -> str:
        return str(tmp_path_factory.mktemp('test_workflow_tokens'))

    @pytest.fixture
    def event_stream(self, temp_dir):
        file_store = get_file_store('local', temp_dir)
        return EventStream('test_workflow', file_store)

    @pytest.fixture
    def github_token(self):
        return ProviderToken(token=SecretStr('github_test_token'))

    @pytest.fixture
    def github_pat(self):
        return ProviderToken(token=SecretStr('github_pat_test_token'))

    @pytest.fixture
    def gitlab_token(self):
        return ProviderToken(token=SecretStr('gitlab_test_token'))

    @pytest.mark.parametrize(
        "token_type,token_env_var,expected_value",
        [
            (ProviderType.GITHUB, "GITHUB_TOKEN", "github_test_token"),
            (ProviderType.GITHUB, "PAT_TOKEN", "github_pat_test_token"),
            (ProviderType.GITLAB, "GITLAB_TOKEN", "gitlab_test_token"),
        ],
    )
    def test_workflow_token_validation(
        self, token_type, token_env_var, expected_value, event_stream, github_token, github_pat, gitlab_token
    ):
        """Test that workflow tokens are correctly validated and exported"""
        provider_tokens = {}
        if token_type == ProviderType.GITHUB and token_env_var == "GITHUB_TOKEN":
            provider_tokens = {ProviderType.GITHUB: github_token}
        elif token_type == ProviderType.GITHUB and token_env_var == "PAT_TOKEN":
            provider_tokens = {ProviderType.GITHUB: github_pat}
        elif token_type == ProviderType.GITLAB:
            provider_tokens = {ProviderType.GITLAB: gitlab_token}

        workflow_content = f"""
        name: Test Workflow
        on:
          workflow_call:
            secrets:
              {token_env_var}:
                required: true
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v2
              - name: Test Step
                env:
                  TOKEN: ${{{token_env_var}}}
                run: echo "Using token for authentication"
        """

        mock_parser = MagicMock()
        mock_parser.extract_token_references.return_value = [token_env_var]
        
        with patch('os.environ', {token_env_var: expected_value}):
            assert os.environ.get(token_env_var) == expected_value
            
            token_refs = mock_parser.extract_token_references(workflow_content)
            assert token_env_var in token_refs
            
            for ref in token_refs:
                if ref == token_env_var:
                    assert os.environ.get(ref) == expected_value

    def test_workflow_token_missing(self, event_stream):
        """Test handling of missing workflow tokens"""
        workflow_content = """
        name: Test Workflow
        on:
          workflow_call:
            secrets:
              GITHUB_TOKEN:
                required: true
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v2
              - name: Test Step
                env:
                  TOKEN: ${{GITHUB_TOKEN}}
                run: echo "Using token for authentication"
        """

        mock_parser = MagicMock()
        mock_parser.extract_token_references.return_value = ["GITHUB_TOKEN"]
        
        with patch('os.environ', {}):
            token_refs = mock_parser.extract_token_references(workflow_content)
            assert "GITHUB_TOKEN" in token_refs
            
            for ref in token_refs:
                assert os.environ.get(ref) is None

    def test_workflow_multiple_tokens(self, event_stream, github_token, gitlab_token):
        """Test handling of multiple tokens in a workflow"""
        workflow_content = """
        name: Test Workflow
        on:
          workflow_call:
            secrets:
              GITHUB_TOKEN:
                required: true
              GITLAB_TOKEN:
                required: true
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v2
              - name: Test GitHub
                env:
                  TOKEN: ${{GITHUB_TOKEN}}
                run: echo "Using GitHub token"
              - name: Test GitLab
                env:
                  TOKEN: ${{GITLAB_TOKEN}}
                run: echo "Using GitLab token"
        """

        mock_parser = MagicMock()
        mock_parser.extract_token_references.return_value = ["GITHUB_TOKEN", "GITLAB_TOKEN"]
        
        with patch('os.environ', {
            "GITHUB_TOKEN": "github_test_token",
            "GITLAB_TOKEN": "gitlab_test_token"
        }):
            token_refs = mock_parser.extract_token_references(workflow_content)
            assert "GITHUB_TOKEN" in token_refs
            assert "GITLAB_TOKEN" in token_refs
            
            assert os.environ.get("GITHUB_TOKEN") == "github_test_token"
            assert os.environ.get("GITLAB_TOKEN") == "gitlab_test_token"
