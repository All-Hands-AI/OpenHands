"""
Predicate extraction utilities for LTL Security Analyzer.

This module converts OpenHands events into sets of atomic predicates
that can be used in Linear Temporal Logic specifications.
"""

import re
from typing import Set, Dict, Any, Optional
from pathlib import Path

from openhands.events.event import Event, EventSource
from openhands.events.action.action import Action
from openhands.events.observation.observation import Observation

# Import specific event types
from openhands.events.action.files import FileReadAction, FileWriteAction, FileEditAction
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.action.browse import BrowseURLAction, BrowseInteractiveAction
from openhands.events.action.agent import ChangeAgentStateAction, AgentFinishAction
from openhands.events.action.mcp import MCPAction

from openhands.events.observation.files import FileReadObservation, FileWriteObservation, FileEditObservation
from openhands.events.observation.commands import CmdOutputObservation, IPythonRunCellObservation
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.events.observation.error import ErrorObservation


class PredicateExtractor:
    """
    Extracts atomic predicates from OpenHands events for LTL analysis.

    Predicates follow the naming convention:
    - action_<type>_<details>: For actions (e.g., "action_file_read", "action_cmd_run")
    - obs_<type>_<details>: For observations (e.g., "obs_file_written", "obs_cmd_error")
    - state_<condition>: For state conditions (e.g., "state_agent_error", "state_high_risk")
    """

    def __init__(self):
        """Initialize the predicate extractor."""
        # Patterns for sensitive file detection
        self.sensitive_file_patterns = [
            r'\.ssh/',
            r'\.env',
            r'\.git/',
            r'id_rsa',
            r'\.pem$',
            r'\.key$',
            r'password',
            r'secret',
            r'config\.json$',
            r'credentials',
        ]

        # Patterns for risky commands
        self.risky_command_patterns = [
            r'sudo\s+',
            r'rm\s+-[rf]+',
            r'chmod\s+[0-7]{3,4}',
            r'wget\s+',
            r'curl\s+',
            r'pip\s+install',
            r'npm\s+install',
            r'git\s+clone',
            r'docker\s+run',
        ]

    def extract_predicates(self, event: Event) -> Set[str]:
        """
        Extract predicates from an event.

        Args:
            event: The event to analyze

        Returns:
            Set of atomic predicates
        """
        predicates = set()

        # Base event predicates
        predicates.update(self._extract_base_predicates(event))

        # Action-specific predicates
        if isinstance(event, Action):
            predicates.update(self._extract_action_predicates(event))

        # Observation-specific predicates
        if isinstance(event, Observation):
            predicates.update(self._extract_observation_predicates(event))

        return predicates

    def _extract_base_predicates(self, event: Event) -> Set[str]:
        """Extract predicates common to all events."""
        predicates = set()

        # Event source
        if hasattr(event, 'source') and event.source:
            predicates.add(f'source_{event.source.value}')

        # Security risk (for actions)
        if hasattr(event, 'security_risk') and event.security_risk:
            risk_level = event.security_risk.name.lower()
            predicates.add(f'security_risk_{risk_level}')

        # High risk shorthand
        if hasattr(event, 'security_risk') and event.security_risk and event.security_risk.value >= 2:
            predicates.add('state_high_risk')

        return predicates

    def _extract_action_predicates(self, action: Action) -> Set[str]:
        """Extract predicates specific to actions."""
        predicates = set()

        # File actions
        if isinstance(action, FileReadAction):
            predicates.update(self._extract_file_read_predicates(action))
        elif isinstance(action, FileWriteAction):
            predicates.update(self._extract_file_write_predicates(action))
        elif isinstance(action, FileEditAction):
            predicates.update(self._extract_file_edit_predicates(action))

        # Command actions
        elif isinstance(action, CmdRunAction):
            predicates.update(self._extract_cmd_run_predicates(action))
        elif isinstance(action, IPythonRunCellAction):
            predicates.update(self._extract_ipython_predicates(action))

        # Browse actions
        elif isinstance(action, BrowseURLAction):
            predicates.update(self._extract_browse_url_predicates(action))
        elif isinstance(action, BrowseInteractiveAction):
            predicates.update(self._extract_browse_interactive_predicates(action))

        # Agent actions
        elif isinstance(action, ChangeAgentStateAction):
            predicates.update(self._extract_agent_state_predicates(action))
        elif isinstance(action, AgentFinishAction):
            predicates.update(self._extract_agent_finish_predicates(action))

        # MCP actions
        elif isinstance(action, MCPAction):
            predicates.update(self._extract_mcp_predicates(action))

        return predicates

    def _extract_observation_predicates(self, observation: Observation) -> Set[str]:
        """Extract predicates specific to observations."""
        predicates = set()

        # File observations
        if isinstance(observation, FileReadObservation):
            predicates.add('obs_file_read_success')
            if hasattr(observation, 'path'):
                predicates.update(self._get_file_predicates(observation.path, 'obs_file_read'))

        elif isinstance(observation, FileWriteObservation):
            predicates.add('obs_file_write_success')
            if hasattr(observation, 'path'):
                predicates.update(self._get_file_predicates(observation.path, 'obs_file_write'))

        elif isinstance(observation, FileEditObservation):
            predicates.add('obs_file_edit_success')
            if hasattr(observation, 'path'):
                predicates.update(self._get_file_predicates(observation.path, 'obs_file_edit'))

        # Command observations
        elif isinstance(observation, CmdOutputObservation):
            predicates.update(self._extract_cmd_output_predicates(observation))

        elif isinstance(observation, IPythonRunCellObservation):
            predicates.add('obs_ipython_success')

        # Browse observations
        elif isinstance(observation, BrowserOutputObservation):
            predicates.update(self._extract_browser_output_predicates(observation))

        # Error observations
        elif isinstance(observation, ErrorObservation):
            predicates.add('obs_error')
            predicates.add('state_error_occurred')

        return predicates

    def _extract_file_read_predicates(self, action: FileReadAction) -> Set[str]:
        """Extract predicates for file read actions."""
        predicates = {'action_file_read'}

        if hasattr(action, 'path'):
            predicates.update(self._get_file_predicates(action.path, 'action_file_read'))

        return predicates

    def _extract_file_write_predicates(self, action: FileWriteAction) -> Set[str]:
        """Extract predicates for file write actions."""
        predicates = {'action_file_write'}

        if hasattr(action, 'path'):
            predicates.update(self._get_file_predicates(action.path, 'action_file_write'))

        return predicates

    def _extract_file_edit_predicates(self, action: FileEditAction) -> Set[str]:
        """Extract predicates for file edit actions."""
        predicates = {'action_file_edit'}

        if hasattr(action, 'path'):
            predicates.update(self._get_file_predicates(action.path, 'action_file_edit'))

        return predicates

    def _extract_cmd_run_predicates(self, action: CmdRunAction) -> Set[str]:
        """Extract predicates for command run actions."""
        predicates = {'action_cmd_run'}

        if hasattr(action, 'command'):
            command = action.command
            predicates.update(self._get_command_predicates(command, 'action_cmd'))

        return predicates

    def _extract_ipython_predicates(self, action: IPythonRunCellAction) -> Set[str]:
        """Extract predicates for IPython actions."""
        predicates = {'action_ipython_run'}

        if hasattr(action, 'code'):
            # Check for potentially risky Python code
            code = action.code.lower()
            if any(keyword in code for keyword in ['subprocess', 'os.system', 'exec', 'eval']):
                predicates.add('action_ipython_system_call')
            if 'import' in code:
                predicates.add('action_ipython_import')

        return predicates

    def _extract_browse_url_predicates(self, action: BrowseURLAction) -> Set[str]:
        """Extract predicates for browse URL actions."""
        predicates = {'action_browse_url'}

        if hasattr(action, 'url'):
            url = action.url
            predicates.update(self._get_url_predicates(url, 'action_browse'))

        return predicates

    def _extract_browse_interactive_predicates(self, action: BrowseInteractiveAction) -> Set[str]:
        """Extract predicates for interactive browse actions."""
        predicates = {'action_browse_interactive'}

        if hasattr(action, 'browser_actions'):
            # TODO: Parse browser actions for specific interaction types
            predicates.add('action_browse_interaction')

        return predicates

    def _extract_agent_state_predicates(self, action: ChangeAgentStateAction) -> Set[str]:
        """Extract predicates for agent state changes."""
        predicates = {'action_agent_state_change'}

        if hasattr(action, 'agent_state'):
            state = action.agent_state
            predicates.add(f'action_agent_state_{state}')
            if state.lower() == 'error':
                predicates.add('state_agent_error')

        return predicates

    def _extract_agent_finish_predicates(self, action: AgentFinishAction) -> Set[str]:
        """Extract predicates for agent finish actions."""
        predicates = {'action_agent_finish'}

        if hasattr(action, 'task_completed'):
            completion = action.task_completed
            if completion:
                predicates.add(f'action_agent_finish_{completion.name.lower()}')

        return predicates

    def _extract_mcp_predicates(self, action: MCPAction) -> Set[str]:
        """Extract predicates for MCP actions."""
        predicates = {'action_mcp_call'}

        if hasattr(action, 'name'):
            tool_name = action.name.replace('-', '_').replace('.', '_')
            predicates.add(f'action_mcp_{tool_name}')

        return predicates

    def _extract_cmd_output_predicates(self, observation: CmdOutputObservation) -> Set[str]:
        """Extract predicates for command output observations."""
        predicates = set()

        if hasattr(observation, 'exit_code'):
            if observation.exit_code == 0:
                predicates.add('obs_cmd_success')
            else:
                predicates.add('obs_cmd_error')
                predicates.add('state_cmd_error')

        if hasattr(observation, 'command'):
            predicates.update(self._get_command_predicates(observation.command, 'obs_cmd'))

        return predicates

    def _extract_browser_output_predicates(self, observation: BrowserOutputObservation) -> Set[str]:
        """Extract predicates for browser output observations."""
        predicates = set()

        if hasattr(observation, 'error') and observation.error:
            predicates.add('obs_browse_error')

        if hasattr(observation, 'url'):
            predicates.update(self._get_url_predicates(observation.url, 'obs_browse'))

        return predicates

    def _get_file_predicates(self, file_path: str, prefix: str) -> Set[str]:
        """Get predicates related to file characteristics."""
        predicates: set[str] = set()

        if not file_path:
            return predicates

        path = Path(file_path)

        # File extension
        if path.suffix:
            ext = path.suffix[1:].lower()  # Remove the dot
            predicates.add(f'{prefix}_ext_{ext}')

        # Sensitive file patterns
        for pattern in self.sensitive_file_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                predicates.add(f'{prefix}_sensitive_file')
                break

        # Hidden files
        if path.name.startswith('.'):
            predicates.add(f'{prefix}_hidden_file')

        # System directories
        if any(part in file_path for part in ['/etc/', '/usr/', '/bin/', '/sbin/']):
            predicates.add(f'{prefix}_system_file')

        return predicates

    def _get_command_predicates(self, command: str, prefix: str) -> Set[str]:
        """Get predicates related to command characteristics."""
        predicates: set[str] = set()

        if not command:
            return predicates

        # Risky command patterns
        for pattern in self.risky_command_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                predicates.add(f'{prefix}_risky')
                predicates.add(f'{prefix}_high_privilege')
                break

        # Network commands
        if any(keyword in command.lower() for keyword in ['wget', 'curl', 'ssh', 'scp', 'ftp']):
            predicates.add(f'{prefix}_network')

        # Package installation
        if any(keyword in command.lower() for keyword in ['install', 'upgrade', 'pip', 'npm', 'apt']):
            predicates.add(f'{prefix}_package_install')

        return predicates

    def _get_url_predicates(self, url: str, prefix: str) -> Set[str]:
        """Get predicates related to URL characteristics."""
        predicates: set[str] = set()

        if not url:
            return predicates

        # External vs local
        if url.startswith(('http://', 'https://')):
            predicates.add(f'{prefix}_external_url')

            # Specific domains (simplified)
            if 'github.com' in url:
                predicates.add(f'{prefix}_github')
            elif any(domain in url for domain in ['google.com', 'stackoverflow.com']):
                predicates.add(f'{prefix}_known_safe')
            else:
                predicates.add(f'{prefix}_unknown_domain')
        else:
            predicates.add(f'{prefix}_local_url')

        return predicates
