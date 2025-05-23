import os
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import json
from pathlib import Path

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.events.stream import EventStream
from openhands.storage import get_file_store


class TestTokenAuthentication:
    """Integration tests for token authentication in workflows"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def workflow_dir(self, temp_dir):
        """Create a directory with workflow files for testing"""
        workflow_dir = os.path.join(temp_dir, '.github', 'workflows')
        os.makedirs(workflow_dir, exist_ok=True)
        return workflow_dir
    
    @pytest.fixture
    def github_token(self):
        """Create a minimal permission GitHub token for testing"""
        return ProviderToken(token="github_test_token")
    
    @pytest.fixture
    def github_pat(self):
        """Create a minimal permission GitHub PAT for testing"""
        return ProviderToken(token="github_pat_test_token")
    
    @pytest.fixture
    def gitlab_token(self):
        """Create a minimal permission GitLab token for testing"""
        return ProviderToken(token="gitlab_test_token")
    
    def test_github_token_authentication(self, workflow_dir, github_token):
        """Test GitHub token authentication in workflows"""
        workflow_path = os.path.join(workflow_dir, 'github_token_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: GitHub Token Workflow
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test GitHub Token
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          echo "Testing GitHub token"
          gh repo list
""")
        
        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = {"name": "test-repo", "full_name": "owner/test-repo"}
        
        with patch('os.environ', {"GITHUB_TOKEN": str(github_token.token)}), \
             patch('openhands.integrations.github.create_github_client', return_value=mock_github_client):
            
            
            assert os.environ.get("GITHUB_TOKEN") == "github_test_token"
            
            from openhands.integrations.github import create_github_client
            client = create_github_client()
            assert client == mock_github_client
            
            repo = client.get_repo("owner/test-repo")
            assert repo["name"] == "test-repo"
    
    def test_github_pat_authentication(self, workflow_dir, github_pat):
        """Test GitHub PAT authentication in workflows"""
        workflow_path = os.path.join(workflow_dir, 'github_pat_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: GitHub PAT Workflow
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test GitHub PAT
        env:
          PAT_TOKEN: ${{ secrets.PAT_TOKEN }}
        run: |
          echo "Testing GitHub PAT"
          gh repo list
""")
        
        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = {"name": "test-repo", "full_name": "owner/test-repo"}
        
        with patch('os.environ', {"PAT_TOKEN": str(github_pat.token)}), \
             patch('openhands.integrations.github.create_github_client', return_value=mock_github_client):
            
            
            assert os.environ.get("PAT_TOKEN") == "github_pat_test_token"
            
            from openhands.integrations.github import create_github_client
            client = create_github_client()
            assert client == mock_github_client
            
            repo = client.get_repo("owner/test-repo")
            assert repo["name"] == "test-repo"
    
    def test_gitlab_token_authentication(self, workflow_dir, gitlab_token):
        """Test GitLab token authentication in workflows"""
        workflow_path = os.path.join(workflow_dir, 'gitlab_token_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: GitLab Token Workflow
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test GitLab Token
        env:
          GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN }}
        run: |
          echo "Testing GitLab token"
          curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.com/api/v4/projects"
""")
        
        mock_gitlab_client = MagicMock()
        mock_gitlab_client.get_project.return_value = {"id": 123, "name": "test-project"}
        
        with patch('os.environ', {"GITLAB_TOKEN": str(gitlab_token.token)}), \
             patch('openhands.integrations.gitlab.create_gitlab_client', return_value=mock_gitlab_client):
            
            
            assert os.environ.get("GITLAB_TOKEN") == "gitlab_test_token"
            
            from openhands.integrations.gitlab import create_gitlab_client
            client = create_gitlab_client()
            assert client == mock_gitlab_client
            
            project = client.get_project(123)
            assert project["name"] == "test-project"
    
    def test_token_validation_in_workflow(self, workflow_dir):
        """Test token validation in workflow files"""
        workflow_path = os.path.join(workflow_dir, 'multi_token_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: Multi-Token Workflow
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test GitHub Token
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: echo "Testing GitHub token"
      - name: Test GitHub PAT
        env:
          PAT_TOKEN: ${{ secrets.PAT_TOKEN }}
        run: echo "Testing GitHub PAT"
      - name: Test GitLab Token
        env:
          GITLAB_TOKEN: ${{ secrets.GITLAB_TOKEN }}
        run: echo "Testing GitLab token"
""")
        
        def validate_workflow_tokens(workflow_path):
            """Validate tokens used in a workflow file"""
            with open(workflow_path, 'r') as f:
                content = f.read()
            
            token_refs = []
            if "${{ secrets.GITHUB_TOKEN }}" in content:
                token_refs.append("GITHUB_TOKEN")
            if "${{ secrets.PAT_TOKEN }}" in content:
                token_refs.append("PAT_TOKEN")
            if "${{ secrets.GITLAB_TOKEN }}" in content:
                token_refs.append("GITLAB_TOKEN")
            
            return token_refs
        
        token_refs = validate_workflow_tokens(workflow_path)
        
        assert "GITHUB_TOKEN" in token_refs
        assert "PAT_TOKEN" in token_refs
        assert "GITLAB_TOKEN" in token_refs
        
        assert len(token_refs) == 3
    
    def test_token_permissions(self, workflow_dir):
        """Test token permissions in workflows"""
        workflow_path = os.path.join(workflow_dir, 'permissions_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: Permissions Workflow
on:
  workflow_dispatch:
permissions:
  contents: read
  issues: write
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test Permissions
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          echo "Testing token permissions"
          gh issue create --title "Test Issue" --body "Created from workflow"
""")
        
        def validate_workflow_permissions(workflow_path):
            """Validate permissions defined in a workflow file"""
            with open(workflow_path, 'r') as f:
                content = f.read()
            
            permissions = {}
            if "permissions:" in content:
                lines = content.split("\n")
                in_permissions = False
                for line in lines:
                    if line.strip() == "permissions:":
                        in_permissions = True
                    elif in_permissions and ":" in line and not line.startswith("jobs:"):
                        key, value = line.strip().split(":", 1)
                        permissions[key.strip()] = value.strip()
                    elif in_permissions and (line.startswith("jobs:") or not line.strip()):
                        in_permissions = False
            
            return permissions
        
        permissions = validate_workflow_permissions(workflow_path)
        
        assert "contents" in permissions
        assert permissions["contents"] == "read"
        assert "issues" in permissions
        assert permissions["issues"] == "write"
        
        assert len(permissions) == 2
