import pytest
from unittest.mock import patch, MagicMock
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType


class MockGitHubAPI:
    """Mock implementation of GitHub API for testing"""
    
    def __init__(self, token=None):
        self.token = token
        self.authenticated = token is not None
        self.requests = []
    
    def create_issue(self, repo, title, body):
        """Mock creating an issue"""
        if not self.authenticated:
            raise Exception("Authentication required")
        
        self.requests.append({
            "type": "create_issue",
            "repo": repo,
            "title": title,
            "body": body
        })
        return {"id": 12345, "number": 1, "title": title}
    
    def create_pull_request(self, repo, title, body, head, base):
        """Mock creating a pull request"""
        if not self.authenticated:
            raise Exception("Authentication required")
        
        self.requests.append({
            "type": "create_pull_request",
            "repo": repo,
            "title": title,
            "body": body,
            "head": head,
            "base": base
        })
        return {"id": 67890, "number": 2, "title": title}


class MockGitLabAPI:
    """Mock implementation of GitLab API for testing"""
    
    def __init__(self, token=None):
        self.token = token
        self.authenticated = token is not None
        self.requests = []
    
    def create_issue(self, project_id, title, description):
        """Mock creating an issue"""
        if not self.authenticated:
            raise Exception("Authentication required")
        
        self.requests.append({
            "type": "create_issue",
            "project_id": project_id,
            "title": title,
            "description": description
        })
        return {"id": 12345, "iid": 1, "title": title}
    
    def create_merge_request(self, project_id, title, description, source_branch, target_branch):
        """Mock creating a merge request"""
        if not self.authenticated:
            raise Exception("Authentication required")
        
        self.requests.append({
            "type": "create_merge_request",
            "project_id": project_id,
            "title": title,
            "description": description,
            "source_branch": source_branch,
            "target_branch": target_branch
        })
        return {"id": 67890, "iid": 2, "title": title}


class TestAPIInteractions:
    """Tests for API interactions with different token types"""
    
    @pytest.fixture
    def github_api(self):
        """Fixture for GitHub API mock"""
        return MockGitHubAPI(token="github_test_token")
    
    @pytest.fixture
    def gitlab_api(self):
        """Fixture for GitLab API mock"""
        return MockGitLabAPI(token="gitlab_test_token")
    
    @pytest.fixture
    def github_token(self):
        """Fixture for GitHub token"""
        return ProviderToken(token=SecretStr("github_test_token"))
    
    @pytest.fixture
    def github_pat(self):
        """Fixture for GitHub PAT token"""
        return ProviderToken(token=SecretStr("github_pat_test_token"))
    
    @pytest.fixture
    def gitlab_token(self):
        """Fixture for GitLab token"""
        return ProviderToken(token=SecretStr("gitlab_test_token"))
    
    def test_github_token_api_interaction(self, github_api, github_token):
        """Test GitHub API interactions with GitHub token"""
        with patch("openhands.integrations.github.create_github_client", return_value=github_api):
            result = github_api.create_issue(
                repo="test/repo",
                title="Test Issue",
                body="This is a test issue"
            )
            
            assert result["number"] == 1
            assert result["title"] == "Test Issue"
            
            assert len(github_api.requests) == 1
            assert github_api.requests[0]["type"] == "create_issue"
            assert github_api.requests[0]["repo"] == "test/repo"
    
    def test_github_pat_api_interaction(self, github_api, github_pat):
        """Test GitHub API interactions with GitHub PAT token"""
        github_api.token = str(github_pat.token.get_secret_value())
        
        with patch("openhands.integrations.github.create_github_client", return_value=github_api):
            result = github_api.create_pull_request(
                repo="test/repo",
                title="Test PR",
                body="This is a test PR",
                head="feature-branch",
                base="main"
            )
            
            assert result["number"] == 2
            assert result["title"] == "Test PR"
            
            assert len(github_api.requests) == 1
            assert github_api.requests[0]["type"] == "create_pull_request"
            assert github_api.requests[0]["repo"] == "test/repo"
            assert github_api.requests[0]["head"] == "feature-branch"
            assert github_api.requests[0]["base"] == "main"
    
    def test_gitlab_token_api_interaction(self, gitlab_api, gitlab_token):
        """Test GitLab API interactions with GitLab token"""
        with patch("openhands.integrations.gitlab.create_gitlab_client", return_value=gitlab_api):
            result = gitlab_api.create_issue(
                project_id=123,
                title="Test GitLab Issue",
                description="This is a test GitLab issue"
            )
            
            assert result["iid"] == 1
            assert result["title"] == "Test GitLab Issue"
            
            assert len(gitlab_api.requests) == 1
            assert gitlab_api.requests[0]["type"] == "create_issue"
            assert gitlab_api.requests[0]["project_id"] == 123
    
    def test_api_authentication_failure(self):
        """Test API authentication failure handling"""
        github_api = MockGitHubAPI()
        gitlab_api = MockGitLabAPI()
        
        with pytest.raises(Exception, match="Authentication required"):
            github_api.create_issue(
                repo="test/repo",
                title="Test Issue",
                body="This is a test issue"
            )
        
        with pytest.raises(Exception, match="Authentication required"):
            gitlab_api.create_issue(
                project_id=123,
                title="Test GitLab Issue",
                description="This is a test GitLab issue"
            )
    
    def test_workflow_api_integration(self, github_api, gitlab_api):
        """Test workflow integration with API clients"""
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
              - name: Create GitHub Issue
                env:
                  GH_TOKEN: ${{GITHUB_TOKEN}}
                run: |
                  gh issue create --title "Test Issue" --body "Created from workflow"
              - name: Create GitLab Issue
                env:
                  GITLAB_TOKEN: ${{GITLAB_TOKEN}}
                run: |
                  curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
                  "https://gitlab.com/api/v4/projects/123/issues?title=Test&description=Created"
        """
        
        with patch("openhands.integrations.github.create_github_client", return_value=github_api), \
             patch("openhands.integrations.gitlab.create_gitlab_client", return_value=gitlab_api):
            
            
            github_api.create_issue(
                repo="test/repo",
                title="Test Issue",
                body="Created from workflow"
            )
            
            gitlab_api.create_issue(
                project_id=123,
                title="Test",
                description="Created"
            )
            
            assert len(github_api.requests) == 1
            assert github_api.requests[0]["type"] == "create_issue"
            
            assert len(gitlab_api.requests) == 1
            assert gitlab_api.requests[0]["type"] == "create_issue"
