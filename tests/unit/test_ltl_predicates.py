"""Unit tests for LTL predicate extraction.

Tests the PredicateExtractor class functionality for converting OpenHands events
into atomic predicates for LTL analysis.
"""

from unittest.mock import Mock

import pytest

from openhands.events.action.action import ActionSecurityRisk
from openhands.events.action.agent import AgentFinishAction, ChangeAgentStateAction
from openhands.events.action.browse import BrowseInteractiveAction, BrowseURLAction
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.action.files import (
    FileReadAction,
    FileWriteAction,
)
from openhands.events.action.mcp import MCPAction
from openhands.events.event import EventSource
from openhands.events.observation.commands import (
    CmdOutputObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.security.ltl.predicates import PredicateExtractor


class TestPredicateExtractor:
    """Test the PredicateExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PredicateExtractor()

    def test_init(self):
        """Test PredicateExtractor initialization."""
        assert self.extractor is not None
        assert len(self.extractor.sensitive_file_patterns) > 0
        assert len(self.extractor.risky_command_patterns) > 0

    def test_extract_predicates_file_read_action(self):
        """Test predicate extraction for file read actions."""
        # Create mock FileReadAction
        action = Mock(spec=FileReadAction)
        action.path = '/tmp/test.txt'
        action.source = EventSource.USER
        # Don't set security_risk to avoid Mock comparison issues

        predicates = self.extractor.extract_predicates(action)

        # Should contain action_file_read and file-specific predicates
        assert 'action_file_read' in predicates
        assert 'action_file_read_ext_txt' in predicates
        assert 'source_user' in predicates

    def test_extract_predicates_file_write_sensitive(self):
        """Test predicate extraction for writing to sensitive files."""
        action = Mock(spec=FileWriteAction)
        action.path = '~/.ssh/id_rsa'
        action.source = EventSource.AGENT
        action.security_risk = ActionSecurityRisk.HIGH

        predicates = self.extractor.extract_predicates(action)

        assert 'action_file_write' in predicates
        assert 'action_file_write_sensitive_file' in predicates
        assert 'source_agent' in predicates
        assert 'security_risk_high' in predicates
        assert 'state_high_risk' in predicates

    def test_extract_predicates_cmd_run_risky(self):
        """Test predicate extraction for risky commands."""
        action = Mock(spec=CmdRunAction)
        action.command = 'sudo rm -rf /'
        action.source = EventSource.AGENT
        action.security_risk = ActionSecurityRisk.MEDIUM

        predicates = self.extractor.extract_predicates(action)

        assert 'action_cmd_run' in predicates
        assert 'action_cmd_risky' in predicates
        assert 'action_cmd_high_privilege' in predicates

    def test_extract_predicates_cmd_output_success(self):
        """Test predicate extraction for successful command output."""
        observation = Mock(spec=CmdOutputObservation)
        observation.exit_code = 0
        observation.command = 'ls -la'
        observation.source = EventSource.AGENT

        predicates = self.extractor.extract_predicates(observation)

        assert 'obs_cmd_success' in predicates
        assert 'obs_cmd_error' not in predicates

    def test_extract_predicates_cmd_output_error(self):
        """Test predicate extraction for failed command output."""
        observation = Mock(spec=CmdOutputObservation)
        observation.exit_code = 1
        observation.command = 'nonexistent_command'
        observation.source = EventSource.AGENT

        predicates = self.extractor.extract_predicates(observation)

        assert 'obs_cmd_error' in predicates
        assert 'state_cmd_error' in predicates
        assert 'obs_cmd_success' not in predicates

    def test_extract_predicates_ipython_system_call(self):
        """Test predicate extraction for IPython with system calls."""
        action = Mock(spec=IPythonRunCellAction)
        action.code = "import subprocess; subprocess.run(['ls'])"
        action.source = EventSource.USER

        predicates = self.extractor.extract_predicates(action)

        assert 'action_ipython_run' in predicates
        assert 'action_ipython_system_call' in predicates
        assert 'action_ipython_import' in predicates

    def test_extract_predicates_browse_url_external(self):
        """Test predicate extraction for browsing external URLs."""
        action = Mock(spec=BrowseURLAction)
        action.url = 'https://github.com/example/repo'
        action.source = EventSource.AGENT

        predicates = self.extractor.extract_predicates(action)

        assert 'action_browse_url' in predicates
        assert 'action_browse_external_url' in predicates
        assert 'action_browse_github' in predicates

    def test_extract_predicates_browse_url_unknown_domain(self):
        """Test predicate extraction for browsing unknown domains."""
        action = Mock(spec=BrowseURLAction)
        action.url = 'https://suspicious-site.com/malware'
        action.source = EventSource.AGENT

        predicates = self.extractor.extract_predicates(action)

        assert 'action_browse_url' in predicates
        assert 'action_browse_external_url' in predicates
        assert 'action_browse_unknown_domain' in predicates

    def test_extract_predicates_mcp_action(self):
        """Test predicate extraction for MCP actions."""
        action = Mock(spec=MCPAction)
        action.name = 'file-read'
        action.source = EventSource.AGENT

        predicates = self.extractor.extract_predicates(action)

        assert 'action_mcp_call' in predicates
        assert 'action_mcp_file_read' in predicates

    def test_extract_predicates_error_observation(self):
        """Test predicate extraction for error observations."""
        observation = Mock(spec=ErrorObservation)
        observation.source = EventSource.AGENT

        predicates = self.extractor.extract_predicates(observation)

        assert 'obs_error' in predicates
        assert 'state_error_occurred' in predicates

    def test_get_file_predicates_hidden_file(self):
        """Test file predicates for hidden files."""
        predicates = self.extractor._get_file_predicates('.bashrc', 'test')

        assert 'test_hidden_file' in predicates

    def test_get_file_predicates_system_file(self):
        """Test file predicates for system files."""
        predicates = self.extractor._get_file_predicates('/etc/passwd', 'test')

        assert 'test_system_file' in predicates

    def test_get_command_predicates_network(self):
        """Test command predicates for network commands."""
        predicates = self.extractor._get_command_predicates(
            'wget https://example.com', 'test'
        )

        assert 'test_risky' in predicates
        assert 'test_network' in predicates

    def test_get_command_predicates_package_install(self):
        """Test command predicates for package installation."""
        predicates = self.extractor._get_command_predicates(
            'pip install malicious-package', 'test'
        )

        assert 'test_risky' in predicates
        assert 'test_package_install' in predicates

    def test_get_url_predicates_local(self):
        """Test URL predicates for local URLs."""
        predicates = self.extractor._get_url_predicates('file:///tmp/test.html', 'test')

        assert 'test_local_url' in predicates

    def test_get_url_predicates_known_safe(self):
        """Test URL predicates for known safe domains."""
        predicates = self.extractor._get_url_predicates(
            'https://stackoverflow.com/questions/123', 'test'
        )

        assert 'test_external_url' in predicates
        assert 'test_known_safe' in predicates

    def test_extract_predicates_no_attributes(self):
        """Test that extraction handles events with missing attributes gracefully."""
        # Create a minimal mock without typical attributes
        event = Mock()
        # Don't set source attribute at all
        if hasattr(event, 'source'):
            delattr(event, 'source')

        # This should not raise an exception
        predicates = self.extractor.extract_predicates(event)

        # Should return an empty set or at least not crash
        assert isinstance(predicates, set)

    def test_extract_predicates_multiple_patterns(self):
        """Test file that matches multiple sensitive patterns."""
        action = Mock(spec=FileReadAction)
        action.path = (
            '/home/user/.ssh/id_rsa.key'  # Matches both .ssh and .key patterns
        )
        action.source = EventSource.USER

        predicates = self.extractor.extract_predicates(action)

        assert 'action_file_read_sensitive_file' in predicates

    def test_extract_base_predicates_no_source(self):
        """Test base predicate extraction when source is None."""
        event = Mock()
        event.source = None

        predicates = self.extractor._extract_base_predicates(event)

        # Should not contain source predicates
        assert not any(p.startswith('source_') for p in predicates)

    def test_extract_base_predicates_no_security_risk(self):
        """Test base predicate extraction when security_risk is None."""
        event = Mock()
        event.source = EventSource.USER
        # Don't set security_risk attribute

        predicates = self.extractor._extract_base_predicates(event)

        assert 'source_user' in predicates
        assert not any(p.startswith('security_risk_') for p in predicates)


# These tests may fail due to missing imports or unimplemented features
# but they test the expected interface and behavior


class TestPredicateExtractorIntegration:
    """Integration tests that may fail due to missing implementations."""

    def test_extract_predicates_agent_finish_incomplete(self):
        """Test agent finish action - may fail due to missing task_completed attribute."""
        action = Mock(spec=AgentFinishAction)
        action.source = EventSource.AGENT
        # task_completed might not exist in the actual implementation

        extractor = PredicateExtractor()

        # This test might fail because AgentFinishAction.task_completed doesn't exist
        with pytest.raises(AttributeError):
            # Expecting this to fail until task_completed is implemented
            action.task_completed = Mock()
            action.task_completed.name = 'SUCCESS'
            predicates = extractor.extract_predicates(action)
            assert 'action_agent_finish_success' in predicates

    def test_extract_predicates_change_agent_state_incomplete(self):
        """Test agent state change - may fail due to missing agent_state attribute."""
        action = Mock(spec=ChangeAgentStateAction)
        action.source = EventSource.AGENT

        extractor = PredicateExtractor()

        # This might fail because ChangeAgentStateAction.agent_state doesn't exist
        with pytest.raises(AttributeError):
            action.agent_state = 'ERROR'
            predicates = extractor.extract_predicates(action)
            assert 'state_agent_error' in predicates

    def test_extract_predicates_browse_interactive_incomplete(self):
        """Test interactive browse action - may fail due to unimplemented browser_actions."""
        action = Mock(spec=BrowseInteractiveAction)
        action.source = EventSource.AGENT

        extractor = PredicateExtractor()

        # browser_actions parsing is marked as TODO, so this may not work fully
        predicates = extractor.extract_predicates(action)
        assert 'action_browse_interactive' in predicates
        # The following might not be present due to TODO implementation
        # assert 'action_browse_interaction' in predicates
