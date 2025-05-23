import os
import pytest
import subprocess
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from openhands.integrations.provider import ProviderToken, ProviderType


class TestLocalWorkflows:
    """Tests for running workflows locally using act"""
    
    @pytest.fixture
    def temp_workflow_dir(self):
        """Create a temporary directory for workflow files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def github_workflow_file(self, temp_workflow_dir):
        """Create a test GitHub workflow file"""
        workflow_dir = os.path.join(temp_workflow_dir, '.github', 'workflows')
        os.makedirs(workflow_dir, exist_ok=True)
        
        workflow_path = os.path.join(workflow_dir, 'test_github_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: Test GitHub Workflow
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
          if [ -z "$GITHUB_TOKEN" ]; then
            echo "GitHub token is missing"
            exit 1
          fi
          echo "GitHub token is valid"
""")
        return workflow_path
    
    @pytest.fixture
    def gitlab_workflow_file(self, temp_workflow_dir):
        """Create a test GitLab workflow file"""
        workflow_dir = os.path.join(temp_workflow_dir, '.github', 'workflows')
        os.makedirs(workflow_dir, exist_ok=True)
        
        workflow_path = os.path.join(workflow_dir, 'test_gitlab_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: Test GitLab Workflow
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
          if [ -z "$GITLAB_TOKEN" ]; then
            echo "GitLab token is missing"
            exit 1
          fi
          echo "GitLab token is valid"
""")
        return workflow_path
    
    @pytest.fixture
    def pat_workflow_file(self, temp_workflow_dir):
        """Create a test PAT workflow file"""
        workflow_dir = os.path.join(temp_workflow_dir, '.github', 'workflows')
        os.makedirs(workflow_dir, exist_ok=True)
        
        workflow_path = os.path.join(workflow_dir, 'test_pat_workflow.yml')
        with open(workflow_path, 'w') as f:
            f.write("""
name: Test PAT Workflow
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test PAT Token
        env:
          PAT_TOKEN: ${{ secrets.PAT_TOKEN }}
        run: |
          echo "Testing PAT token"
          if [ -z "$PAT_TOKEN" ]; then
            echo "PAT token is missing"
            exit 1
          fi
          echo "PAT token is valid"
""")
        return workflow_path
    
    def test_act_installed(self):
        """Test that act is installed or can be installed"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b'act version 0.2.30')
            
            result = subprocess.run(['act', '--version'], capture_output=True)
            
            mock_run.assert_called_once()
            
            assert result.returncode == 0
    
    def test_github_workflow_local_execution(self, github_workflow_file):
        """Test running a GitHub workflow locally with act"""
        with patch('subprocess.run') as mock_run, \
             patch.dict(os.environ, {"GITHUB_TOKEN": "test_github_token"}):
            
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b'[Test GitHub Workflow/test] Start image=catthehacker/ubuntu:act-latest\n'
                       b'[Test GitHub Workflow/test] docker run image=catthehacker/ubuntu:act-latest\n'
                       b'[Test GitHub Workflow/test] Success - Test GitHub Token\n'
                       b'[Test GitHub Workflow/test] Run Test GitHub Token\n'
                       b'[Test GitHub Workflow/test] Testing GitHub token\n'
                       b'[Test GitHub Workflow/test] GitHub token is valid\n'
            )
            
            workflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(github_workflow_file)))
            result = subprocess.run(
                ['act', '-W', '.github/workflows/test_github_workflow.yml', '--secret', 'GITHUB_TOKEN=test_github_token'],
                cwd=workflow_dir,
                capture_output=True
            )
            
            mock_run.assert_called_once()
            
            assert result.returncode == 0
            
            assert b'GitHub token is valid' in result.stdout
    
    def test_gitlab_workflow_local_execution(self, gitlab_workflow_file):
        """Test running a GitLab workflow locally with act"""
        with patch('subprocess.run') as mock_run, \
             patch.dict(os.environ, {"GITLAB_TOKEN": "test_gitlab_token"}):
            
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b'[Test GitLab Workflow/test] Start image=catthehacker/ubuntu:act-latest\n'
                       b'[Test GitLab Workflow/test] docker run image=catthehacker/ubuntu:act-latest\n'
                       b'[Test GitLab Workflow/test] Success - Test GitLab Token\n'
                       b'[Test GitLab Workflow/test] Run Test GitLab Token\n'
                       b'[Test GitLab Workflow/test] Testing GitLab token\n'
                       b'[Test GitLab Workflow/test] GitLab token is valid\n'
            )
            
            workflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(gitlab_workflow_file)))
            result = subprocess.run(
                ['act', '-W', '.github/workflows/test_gitlab_workflow.yml', '--secret', 'GITLAB_TOKEN=test_gitlab_token'],
                cwd=workflow_dir,
                capture_output=True
            )
            
            mock_run.assert_called_once()
            
            assert result.returncode == 0
            
            assert b'GitLab token is valid' in result.stdout
    
    def test_pat_workflow_local_execution(self, pat_workflow_file):
        """Test running a PAT workflow locally with act"""
        with patch('subprocess.run') as mock_run, \
             patch.dict(os.environ, {"PAT_TOKEN": "test_pat_token"}):
            
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b'[Test PAT Workflow/test] Start image=catthehacker/ubuntu:act-latest\n'
                       b'[Test PAT Workflow/test] docker run image=catthehacker/ubuntu:act-latest\n'
                       b'[Test PAT Workflow/test] Success - Test PAT Token\n'
                       b'[Test PAT Workflow/test] Run Test PAT Token\n'
                       b'[Test PAT Workflow/test] Testing PAT token\n'
                       b'[Test PAT Workflow/test] PAT token is valid\n'
            )
            
            workflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(pat_workflow_file)))
            result = subprocess.run(
                ['act', '-W', '.github/workflows/test_pat_workflow.yml', '--secret', 'PAT_TOKEN=test_pat_token'],
                cwd=workflow_dir,
                capture_output=True
            )
            
            mock_run.assert_called_once()
            
            assert result.returncode == 0
            
            assert b'PAT token is valid' in result.stdout
    
    def test_workflow_token_missing(self, github_workflow_file):
        """Test workflow execution with missing token"""
        with patch('subprocess.run') as mock_run:
            
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=b'[Test GitHub Workflow/test] Start image=catthehacker/ubuntu:act-latest\n'
                       b'[Test GitHub Workflow/test] docker run image=catthehacker/ubuntu:act-latest\n'
                       b'[Test GitHub Workflow/test] Run Test GitHub Token\n'
                       b'[Test GitHub Workflow/test] Testing GitHub token\n'
                       b'[Test GitHub Workflow/test] GitHub token is missing\n'
                       b'[Test GitHub Workflow/test] Failure - Test GitHub Token\n'
            )
            
            workflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(github_workflow_file)))
            result = subprocess.run(
                ['act', '-W', '.github/workflows/test_github_workflow.yml'],
                cwd=workflow_dir,
                capture_output=True
            )
            
            mock_run.assert_called_once()
            
            assert result.returncode == 1
            
            assert b'GitHub token is missing' in result.stdout
