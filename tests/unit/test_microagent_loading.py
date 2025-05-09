import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from unittest import mock

import pytest

from openhands.core.config import AppConfig
from openhands.events.observation import (
    CmdOutputObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.microagent import (
    KnowledgeMicroagent,
    RepoMicroagent,
)
from openhands.runtime.base import Runtime
from openhands.runtime.utils.git_handler import CommandResult


class TestMicroagentLoading:
    @pytest.fixture
    def temp_user_microagents_dir(self):
        # Create a temporary directory to simulate the user's ~/.openhands/microagents directory
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after the test
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_runtime_instance(self, temp_user_microagents_dir):
        """Creates a mock Runtime instance with a mocked config."""
        runtime_instance = mock.MagicMock(spec=Runtime)
        mock_config = mock.MagicMock(spec=AppConfig)
        # Set the custom dir to our temp fixture path
        mock_config.custom_microagents_dir = temp_user_microagents_dir
        # Set a dummy workspace path
        mock_config.workspace_mount_path_in_sandbox = '/workspace'
        runtime_instance.config = mock_config

        # Mock the abstract methods
        runtime_instance.run = mock.MagicMock(
            return_value=CmdOutputObservation(
                command_id=-1, command='', exit_code=0, content=''
            )
        )
        runtime_instance.run_action = mock.MagicMock(
            return_value=CmdOutputObservation(
                command_id=-1, command='', exit_code=0, content=''
            )
        )
        runtime_instance.call_tool_mcp = mock.AsyncMock(
            return_value=CmdOutputObservation(
                command_id=-1, command='', exit_code=0, content=''
            )
        )
        runtime_instance.list_files = mock.MagicMock(return_value=[])
        runtime_instance.copy_from = mock.MagicMock(return_value=Path('/tmp/test.zip'))
        runtime_instance.copy_to = mock.MagicMock()
        runtime_instance._execute_shell_fn_git_handler = mock.MagicMock(
            return_value=CommandResult(content='', exit_code=0)
        )
        runtime_instance.read = mock.MagicMock(
            return_value=FileReadObservation(content='', path='')
        )
        runtime_instance.write = mock.MagicMock(
            return_value=FileWriteObservation(path='', content='')
        )
        runtime_instance.run_ipython = mock.MagicMock(
            return_value=CmdOutputObservation(
                command_id=-1, command='', exit_code=0, content=''
            )
        )

        # Mock the _load_microagents_from_dir method to call the actual implementation
        runtime_instance._load_microagents_from_dir = (
            Runtime._load_microagents_from_dir.__get__(runtime_instance)
        )

        # Mock the get_microagents_from_selected_repo method to call the actual implementation
        runtime_instance.get_microagents_from_selected_repo = (
            Runtime.get_microagents_from_selected_repo.__get__(runtime_instance)
        )

        return runtime_instance

    def test_runtime_loads_microagents_from_directory(self):
        """Test that Runtime._load_microagents_from_dir loads agents correctly."""
        # Define test repo microagent
        # Define test knowledge microagent
        knowledge_content = """---
name: test-knowledge
type: knowledge
triggers:
  - test trigger
---
# Test Knowledge
This is a test knowledge microagent.
"""
        repo_content = """---
name: test-repo
type: repo
---
# Test Repo
This is a test repo microagent.
"""
        # Define the simulated sandbox directory path
        sandbox_dir_path = Path('/workspace/sandbox_microagents')
        knowledge_sandbox_path = str(sandbox_dir_path / 'test-knowledge.md')
        repo_sandbox_path = str(sandbox_dir_path / 'test-repo.md')

        # Create a mock Runtime instance
        runtime_instance = mock.MagicMock(spec=Runtime)
        runtime_instance.config = mock.MagicMock(spec=AppConfig)

        # Mock list_files to return the simulated files in the sandbox directory
        def list_files_side_effect(path):
            if path == str(sandbox_dir_path):
                return [
                    knowledge_sandbox_path,
                    repo_sandbox_path,
                ]
            return []

        runtime_instance.list_files.side_effect = list_files_side_effect

        # Mock copy_from to return a path to a temporary zip file containing the agents
        temp_zip_file = None
        try:
            # Create a temporary zip file locally
            temp_zip_fd, temp_zip_path_str = tempfile.mkstemp(suffix='.zip')
            os.close(temp_zip_fd)
            temp_zip_path = Path(temp_zip_path_str)
            temp_zip_file = temp_zip_path  # Store for cleanup

            with zipfile.ZipFile(temp_zip_path, 'w') as zf:
                # Add the microagent files to the zip, simulating the structure inside the sandbox dir
                # Note: zipfile expects relative paths for archive names usually,
                # but load_microagents_from_dir extracts all, so structure matters.
                # Let's simulate the extraction target structure.
                zf.writestr('test-knowledge.md', knowledge_content)
                zf.writestr('test-repo.md', repo_content)

            runtime_instance.copy_from.return_value = temp_zip_path

            # Mock the logger
            with mock.patch('openhands.runtime.base.logger') as mock_logger:
                # Call the method under test
                loaded_agents = Runtime._load_microagents_from_dir(
                    runtime_instance, sandbox_dir_path
                )

            # Assertions
            assert len(loaded_agents) == 2
            runtime_instance.list_files.assert_called_once_with(str(sandbox_dir_path))
            runtime_instance.copy_from.assert_called_once_with(str(sandbox_dir_path))
            mock_logger.error.assert_not_called()  # Check for loading errors

            knowledge_agent_found = False
            repo_agent_found = False
            for agent in loaded_agents:
                if (
                    isinstance(agent, KnowledgeMicroagent)
                    and agent.name == 'test-knowledge'
                ):
                    knowledge_agent_found = True
                    assert agent.triggers == ['test trigger']
                    assert 'This is a test knowledge microagent.' in agent.content
                    # Check the source attribute ends with the expected filename
                    assert agent.source.endswith('test-knowledge.md')
                    # microagent_dir is the temp extraction dir, difficult to assert precisely without more mocking
                    # assert agent.microagent_dir == ???
                elif isinstance(agent, RepoMicroagent) and agent.name == 'test-repo':
                    repo_agent_found = True
                    assert 'This is a test repo microagent.' in agent.content
                    assert agent.source.endswith('test-repo.md')
                    # assert agent.microagent_dir == ???

            assert knowledge_agent_found, 'Knowledge microagent not loaded correctly'
            assert repo_agent_found, 'Repo microagent not loaded correctly'

        finally:
            # Clean up the temporary zip file
            # Clean up the temporary zip file
            if temp_zip_file and temp_zip_file.exists():
                temp_zip_file.unlink()

    @mock.patch('os.path.exists')
    def test_get_microagents_loads_from_custom_dir(
        self,
        mock_os_path_exists,
        mock_runtime_instance,
        temp_user_microagents_dir,
    ):
        """Test get_microagents_from_selected_repo loads from the custom directory.

        This test creates actual microagent files in a temporary directory,
        configures the mock Runtime instance to use this directory as the custom
        microagents directory, and verifies that the microagents are loaded correctly.
        """
        # Set up os.path.exists to return True for the custom directory
        mock_os_path_exists.return_value = True
        # Create actual microagent files in the temporary directory
        knowledge_agent_content = """---
name: custom-knowledge-agent
type: knowledge
triggers:
  - custom knowledge trigger
---
# Custom Knowledge Agent
This is a custom knowledge microagent.
"""
        repo_agent_content = """---
name: custom-repo-agent
type: repo
---
# Custom Repo Agent
This is a custom repo microagent.
"""

        # Write the files to the temporary directory
        knowledge_agent_path = os.path.join(
            temp_user_microagents_dir, 'custom-knowledge-agent.md'
        )
        repo_agent_path = os.path.join(
            temp_user_microagents_dir, 'custom-repo-agent.md'
        )

        with open(knowledge_agent_path, 'w') as f:
            f.write(knowledge_agent_content)
        with open(repo_agent_path, 'w') as f:
            f.write(repo_agent_content)

        # Define expected sandbox path for the copied custom agents
        sandbox_custom_dir = Path('/workspace/.custom_microagents')

        # Mock the run_action for mkdir
        mock_runtime_instance.run_action.return_value = CmdOutputObservation(
            command_id=-1, command='', exit_code=0, content=''
        )

        # Mock list_files to return the simulated files in the sandbox directory
        def list_files_side_effect(path):
            if path == str(
                mock_runtime_instance.config.workspace_mount_path_in_sandbox
            ):
                return []  # No user directories for this test
            elif path == str(sandbox_custom_dir):
                return [
                    str(sandbox_custom_dir / 'custom-knowledge-agent.md'),
                    str(sandbox_custom_dir / 'custom-repo-agent.md'),
                ]
            return []

        mock_runtime_instance.list_files.side_effect = list_files_side_effect

        # Mock copy_from to return a path to a temporary zip file containing the agents
        temp_zip_file = None
        try:
            # Create a temporary zip file locally
            temp_zip_fd, temp_zip_path_str = tempfile.mkstemp(suffix='.zip')
            os.close(temp_zip_fd)
            temp_zip_path = Path(temp_zip_path_str)
            temp_zip_file = temp_zip_path  # Store for cleanup

            with zipfile.ZipFile(temp_zip_path, 'w') as zf:
                # Add the microagent files to the zip
                zf.writestr('custom-knowledge-agent.md', knowledge_agent_content)
                zf.writestr('custom-repo-agent.md', repo_agent_content)

            mock_runtime_instance.copy_from.return_value = temp_zip_path

            # Call the method under test (no selected repo)
            loaded_agents = mock_runtime_instance.get_microagents_from_selected_repo(
                selected_repository=None
            )

            # Verify the expected methods were called
            mock_runtime_instance.run_action.assert_called_once()
            args, _ = mock_runtime_instance.run_action.call_args
            assert args[0].command == f'mkdir -p {sandbox_custom_dir}'

            mock_runtime_instance.copy_to.assert_called_once_with(
                temp_user_microagents_dir, str(sandbox_custom_dir), recursive=True
            )

            mock_runtime_instance.list_files.assert_called_with(str(sandbox_custom_dir))
            mock_runtime_instance.copy_from.assert_called_with(str(sandbox_custom_dir))

            # Verify the loaded agents
            assert len(loaded_agents) == 2

            # Check for the knowledge agent
            knowledge_agent_found = False
            repo_agent_found = False

            for agent in loaded_agents:
                if (
                    isinstance(agent, KnowledgeMicroagent)
                    and agent.name == 'custom-knowledge-agent'
                ):
                    knowledge_agent_found = True
                    assert agent.triggers == ['custom knowledge trigger']
                    assert 'This is a custom knowledge microagent.' in agent.content
                    assert agent.source.endswith('custom-knowledge-agent.md')
                elif (
                    isinstance(agent, RepoMicroagent)
                    and agent.name == 'custom-repo-agent'
                ):
                    repo_agent_found = True
                    assert 'This is a custom repo microagent.' in agent.content
                    assert agent.source.endswith('custom-repo-agent.md')

            assert knowledge_agent_found, 'Knowledge microagent not loaded correctly'
            assert repo_agent_found, 'Repo microagent not loaded correctly'

        finally:
            # Clean up the temporary zip file
            if temp_zip_file and temp_zip_file.exists():
                temp_zip_file.unlink()

    def test_get_microagents_loads_from_multiple_sources(
        self, mock_runtime_instance, temp_user_microagents_dir
    ):
        """Test get_microagents_from_selected_repo loads and combines agents from multiple sources.

        This test creates actual microagent files for each source (custom dir, user repo,
        and selected repo), configures the mock Runtime instance to use these directories,
        and verifies that the microagents are loaded correctly from all sources.
        """
        # Setup paths
        workspace_root = Path(
            mock_runtime_instance.config.workspace_mount_path_in_sandbox
        )
        selected_repo_name = 'test/repo'
        user_dir_name = 'testuser'
        repo_base_name = selected_repo_name.split('/')[-1]

        sandbox_custom_dir = workspace_root / '.custom_microagents'
        sandbox_user_dir = workspace_root / user_dir_name
        sandbox_user_microagents_dir = sandbox_user_dir / '.openhands' / 'microagents'
        sandbox_repo_root = workspace_root / repo_base_name
        sandbox_repo_microagents_dir = sandbox_repo_root / '.openhands' / 'microagents'

        # 1. Create custom agent in local temp dir
        custom_agent_content = """---
name: custom-agent
type: knowledge
triggers:
  - custom trigger
---
# Custom Agent
This is a custom agent from the custom directory.
"""
        custom_agent_local_path = os.path.join(
            temp_user_microagents_dir, 'custom-agent.md'
        )
        with open(custom_agent_local_path, 'w') as f:
            f.write(custom_agent_content)

        # 2. Create content for user and repo agents
        user_agent_content = """---
name: user-agent
type: knowledge
triggers:
  - user trigger
---
# User Agent
This is a user agent from the user's .openhands repository.
"""

        repo_agent_content = """---
name: repo-agent
type: repo
---
# Repo Agent
This is a repo agent from the repository's .openhands directory.
"""

        # 3. Mock environment and interactions
        with mock.patch('os.path.exists', return_value=True):
            # Mock list_files to find the user dir and files in each directory
            def list_files_side_effect(path):
                if path == str(workspace_root):
                    return [f'{user_dir_name}/']
                elif path == str(sandbox_custom_dir):
                    return [str(sandbox_custom_dir / 'custom-agent.md')]
                elif path == str(sandbox_user_microagents_dir):
                    return [str(sandbox_user_microagents_dir / 'user-agent.md')]
                elif path == str(sandbox_repo_microagents_dir):
                    return [str(sandbox_repo_microagents_dir / 'repo-agent.md')]
                else:
                    return []

            mock_runtime_instance.list_files.side_effect = list_files_side_effect

            # Mock run_action for mkdir and user dir check
            def run_action_side_effect(action):
                if action.command == f'mkdir -p {sandbox_custom_dir}':
                    return CmdOutputObservation(
                        command_id=-1, command='', exit_code=0, content=''
                    )
                elif (
                    action.command
                    == f'[ -d "{sandbox_user_dir / ".openhands"}" ] && echo "exists" || echo "not exists"'
                ):
                    return CmdOutputObservation(
                        command_id=-1, command='', exit_code=0, content='exists'
                    )
                else:
                    return CmdOutputObservation(
                        command_id=-1, command='', exit_code=0, content='not exists'
                    )

            mock_runtime_instance.run_action.side_effect = run_action_side_effect

            # Mock copy_from to return appropriate zip files for each directory
            def copy_from_side_effect(path):
                temp_zip_fd, temp_zip_path_str = tempfile.mkstemp(suffix='.zip')
                os.close(temp_zip_fd)
                temp_zip_path = Path(temp_zip_path_str)

                with zipfile.ZipFile(temp_zip_path, 'w') as zf:
                    if path == str(sandbox_custom_dir):
                        zf.writestr('custom-agent.md', custom_agent_content)
                    elif path == str(sandbox_user_microagents_dir):
                        zf.writestr('user-agent.md', user_agent_content)
                    elif path == str(sandbox_repo_microagents_dir):
                        zf.writestr('repo-agent.md', repo_agent_content)

                return temp_zip_path

            mock_runtime_instance.copy_from.side_effect = copy_from_side_effect

            # 4. Call the method under test
            loaded_agents = mock_runtime_instance.get_microagents_from_selected_repo(
                selected_repository=selected_repo_name
            )

            # 5. Verify the expected methods were called
            mock_runtime_instance.copy_to.assert_called_with(
                temp_user_microagents_dir, str(sandbox_custom_dir), recursive=True
            )

            # 6. Verify the loaded agents
            assert len(loaded_agents) == 3

            agent_types = {}
            for agent in loaded_agents:
                agent_types[agent.name] = type(agent)

                if agent.name == 'custom-agent':
                    assert isinstance(agent, KnowledgeMicroagent)
                    assert agent.triggers == ['custom trigger']
                    assert (
                        'This is a custom agent from the custom directory.'
                        in agent.content
                    )
                elif agent.name == 'user-agent':
                    assert isinstance(agent, KnowledgeMicroagent)
                    assert agent.triggers == ['user trigger']
                    assert (
                        "This is a user agent from the user's .openhands repository."
                        in agent.content
                    )
                elif agent.name == 'repo-agent':
                    assert isinstance(agent, RepoMicroagent)
                    assert (
                        "This is a repo agent from the repository's .openhands directory."
                        in agent.content
                    )

            assert 'custom-agent' in agent_types, 'Custom agent not loaded'
            assert 'user-agent' in agent_types, 'User agent not loaded'
            assert 'repo-agent' in agent_types, 'Repo agent not loaded'

    def test_get_microagents_loads_from_user_org_repos(self, mock_runtime_instance):
        """Test get_microagents_from_selected_repo loads from user/org .openhands dirs.

        This test creates actual microagent files for user and org repos,
        configures the mock Runtime instance to use these directories,
        and verifies that the microagents are loaded correctly from both sources.
        """
        workspace_root = Path(
            mock_runtime_instance.config.workspace_mount_path_in_sandbox
        )
        user_dir_name = 'testuser'
        org_dir_name = 'testorg'
        sandbox_user_dir = workspace_root / user_dir_name
        sandbox_org_dir = workspace_root / org_dir_name
        sandbox_user_microagents_dir = sandbox_user_dir / '.openhands' / 'microagents'
        sandbox_org_microagents_dir = sandbox_org_dir / '.openhands' / 'microagents'

        # Create content for user and org agents
        user_agent_content = """---
name: user-agent
type: knowledge
triggers:
  - user trigger
---
# User Agent
This is a user agent from the user's .openhands repository.
"""

        org_agent_content = """---
name: org-agent
type: repo
---
# Org Agent
This is an org agent from the organization's .openhands repository.
"""

        # Mock environment and interactions
        with mock.patch('os.path.exists', return_value=False):
            # Mock list_files to return the simulated user/org dirs and files
            def list_files_side_effect(path):
                if path == str(workspace_root):
                    return [
                        f'{user_dir_name}/',
                        f'{org_dir_name}/',
                        'some_other_file.txt',  # Should be ignored
                    ]
                elif path == str(sandbox_user_microagents_dir):
                    return [str(sandbox_user_microagents_dir / 'user-agent.md')]
                elif path == str(sandbox_org_microagents_dir):
                    return [str(sandbox_org_microagents_dir / 'org-agent.md')]
                else:
                    return []

            mock_runtime_instance.list_files.side_effect = list_files_side_effect

            # Mock run_action to simulate checking for .openhands dir existence
            def run_action_side_effect(action):
                if (
                    action.command
                    == f'[ -d "{sandbox_user_dir / ".openhands"}" ] && echo "exists" || echo "not exists"'
                ):
                    return CmdOutputObservation(
                        command_id=-1, command='', exit_code=0, content='exists'
                    )
                elif (
                    action.command
                    == f'[ -d "{sandbox_org_dir / ".openhands"}" ] && echo "exists" || echo "not exists"'
                ):
                    return CmdOutputObservation(
                        command_id=-1, command='', exit_code=0, content='exists'
                    )
                else:
                    # Default for other potential checks
                    return CmdOutputObservation(
                        command_id=-1, command='', exit_code=0, content='not exists'
                    )

            mock_runtime_instance.run_action.side_effect = run_action_side_effect

            # Mock copy_from to return appropriate zip files for each directory
            def copy_from_side_effect(path):
                temp_zip_fd, temp_zip_path_str = tempfile.mkstemp(suffix='.zip')
                os.close(temp_zip_fd)
                temp_zip_path = Path(temp_zip_path_str)

                with zipfile.ZipFile(temp_zip_path, 'w') as zf:
                    if path == str(sandbox_user_microagents_dir):
                        zf.writestr('user-agent.md', user_agent_content)
                    elif path == str(sandbox_org_microagents_dir):
                        zf.writestr('org-agent.md', org_agent_content)

                return temp_zip_path

            mock_runtime_instance.copy_from.side_effect = copy_from_side_effect

            # Call the method under test (no selected repo, focus on user/org)
            loaded_agents = mock_runtime_instance.get_microagents_from_selected_repo(
                selected_repository=None
            )

            # Verify the expected methods were called
            mock_runtime_instance.list_files.assert_any_call(str(workspace_root))

            # Verify the loaded agents
            assert len(loaded_agents) == 2

            agent_types = {}
            for agent in loaded_agents:
                agent_types[agent.name] = type(agent)

                if agent.name == 'user-agent':
                    assert isinstance(agent, KnowledgeMicroagent)
                    assert agent.triggers == ['user trigger']
                    assert (
                        "This is a user agent from the user's .openhands repository."
                        in agent.content
                    )
                elif agent.name == 'org-agent':
                    assert isinstance(agent, RepoMicroagent)
                    assert (
                        "This is an org agent from the organization's .openhands repository."
                        in agent.content
                    )

            assert 'user-agent' in agent_types, 'User agent not loaded'
            assert 'org-agent' in agent_types, 'Org agent not loaded'

    def test_get_microagents_loads_from_selected_repo(self, mock_runtime_instance):
        """Test get_microagents_from_selected_repo loads from the selected repo dir.

        This test creates actual microagent files for the selected repository,
        configures the mock Runtime instance to use this directory,
        and verifies that the microagents are loaded correctly.
        """
        selected_repo_name = 'test/repo'
        repo_base_name = selected_repo_name.split('/')[-1]  # 'repo'
        sandbox_repo_root = Path('/workspace') / repo_base_name
        sandbox_repo_microagents_dir = sandbox_repo_root / '.openhands' / 'microagents'

        # Create content for repo agent
        repo_agent_content = """---
name: repo-agent
type: repo
---
# Repo Agent
This is a repo agent from the repository's .openhands directory.
"""

        # Mock environment and interactions
        with mock.patch('os.path.exists', return_value=False):
            # Mock list_files to return empty for workspace root (to skip user/org checks)
            # and return the repo agent file for the repo microagents dir
            def list_files_side_effect(path):
                if path == str(
                    mock_runtime_instance.config.workspace_mount_path_in_sandbox
                ):
                    return []  # No user/org dirs found
                elif path == str(sandbox_repo_microagents_dir):
                    return [str(sandbox_repo_microagents_dir / 'repo-agent.md')]
                else:
                    return []

            mock_runtime_instance.list_files.side_effect = list_files_side_effect

            # Mock run_action to return 'not exists' for user/org dir checks
            mock_runtime_instance.run_action.return_value = CmdOutputObservation(
                command_id=-1, command='', exit_code=0, content='not exists'
            )

            # Mock copy_from to return a zip file containing the repo agent
            def copy_from_side_effect(path):
                temp_zip_fd, temp_zip_path_str = tempfile.mkstemp(suffix='.zip')
                os.close(temp_zip_fd)
                temp_zip_path = Path(temp_zip_path_str)

                with zipfile.ZipFile(temp_zip_path, 'w') as zf:
                    if path == str(sandbox_repo_microagents_dir):
                        zf.writestr('repo-agent.md', repo_agent_content)

                return temp_zip_path

            mock_runtime_instance.copy_from.side_effect = copy_from_side_effect

            # Call the method under test with a selected repo
            loaded_agents = mock_runtime_instance.get_microagents_from_selected_repo(
                selected_repository=selected_repo_name
            )

            # Verify the expected methods were called
            mock_runtime_instance.list_files.assert_any_call(
                str(sandbox_repo_microagents_dir)
            )
            mock_runtime_instance.copy_from.assert_called_with(
                str(sandbox_repo_microagents_dir)
            )

            # Verify the loaded agents
            assert len(loaded_agents) == 1

            assert loaded_agents[0].name == 'repo-agent'
            assert isinstance(loaded_agents[0], RepoMicroagent)
            assert (
                "This is a repo agent from the repository's .openhands directory."
                in loaded_agents[0].content
            )
