"""Command approval analyzer for security."""

import re
from typing import Any, Dict, List

import bashlex
from fastapi import Request

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.security.analyzer import SecurityAnalyzer


class CommandPattern:
    """A pattern for matching commands."""

    def __init__(self, pattern: str, description: str):
        """Initialize a new command pattern.
        
        Args:
            pattern: The regex pattern to match commands against.
            description: A human-readable description of what this pattern matches.
        """
        self.pattern = pattern
        self.description = description
        self._compiled_pattern = re.compile(pattern)
        
    def matches(self, command: str) -> bool:
        """Check if the command matches this pattern.
        
        Args:
            command: The command to check.
            
        Returns:
            bool: True if the command matches, False otherwise.
        """
        return bool(self._compiled_pattern.match(command))


class CommandParser:
    """Parser for bash commands using bashlex."""
    
    def is_piped_command(self, command: str) -> bool:
        """Check if a command contains pipes.
        
        Args:
            command: The command to check.
            
        Returns:
            bool: True if the command contains pipes, False otherwise.
        """
        if not command or not command.strip():
            return False
            
        try:
            parts = bashlex.parse(command)
            for part in parts:
                if part.kind == 'pipeline':
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error parsing command with bashlex: {e}")
            # Fallback: check for pipe character not in quotes
            # This is a simple heuristic and not as accurate as bashlex parsing
            in_single_quote = False
            in_double_quote = False
            for char in command:
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif char == '|' and not in_single_quote and not in_double_quote:
                    return True
            return False
    
    def parse_command(self, command: str) -> List[str]:
        """Parse a command into individual parts, handling pipes.
        
        Args:
            command: The command to parse.
            
        Returns:
            List[str]: List of individual commands.
        """
        if not command or not command.strip():
            return []
            
        try:
            parts = bashlex.parse(command)
            commands = []
            
            # Helper function to extract command from a node
            def extract_command(node):
                if node.kind == 'command':
                    cmd_parts = []
                    for part in node.parts:
                        if hasattr(part, 'word'):
                            cmd_parts.append(part.word)
                    if cmd_parts:
                        return ' '.join(cmd_parts)
                return None
            
            # Process the AST
            for part in parts:
                if part.kind == 'pipeline':
                    # A pipeline has multiple commands
                    for subpart in part.parts:
                        if subpart.kind == 'command':
                            cmd = extract_command(subpart)
                            if cmd:
                                commands.append(cmd)
                elif part.kind == 'command':
                    # A single command
                    cmd = extract_command(part)
                    if cmd:
                        commands.append(cmd)
                elif part.kind == 'list':
                    # A list of commands (e.g., with && or ||)
                    # We only take the first command for approval purposes
                    for subpart in part.parts:
                        if subpart.kind == 'command':
                            cmd = extract_command(subpart)
                            if cmd:
                                commands.append(cmd)
                                break
                        elif subpart.kind == 'operator':
                            # Stop at the first operator
                            break
                    
            return commands
        except Exception as e:
            logger.warning(f"Error parsing command with bashlex: {e}")
            # Fallback: simple split by pipe
            # This is a simple heuristic and not as accurate as bashlex parsing
            if '|' in command:
                return [part.strip() for part in command.split('|') if part.strip()]
            else:
                return [command.strip()] if command.strip() else []


class CommandApprovalAnalyzer(SecurityAnalyzer):
    """Security analyzer that automatically approves commands based on patterns and previously approved commands."""

    def __init__(
        self,
        event_stream: EventStream,
        policy: str | None = None,
        sid: str | None = None,
    ) -> None:
        """Initializes a new instance of the CommandApprovalAnalyzer class."""
        super().__init__(event_stream)
        self.parser = CommandParser()
        self.approved_commands: Dict[str, bool] = {}  # Dict of exact commands that have been approved
        self.approved_patterns: List[CommandPattern] = []  # List of regex patterns for approved commands
        
        # Add some default patterns
        self._add_default_patterns()
    
    def _add_default_patterns(self) -> None:
        """Add default command patterns that are always approved."""
        # Simple, safe commands
        self.approved_patterns.append(
            CommandPattern(
                pattern=r"^ls(\s+-[a-zA-Z]+)*(\s+\S+)*$",
                description="List directory contents"
            )
        )
        self.approved_patterns.append(
            CommandPattern(
                pattern=r"^cd(\s+\S+)?$",
                description="Change directory"
            )
        )
        self.approved_patterns.append(
            CommandPattern(
                pattern=r"^pwd$",
                description="Print working directory"
            )
        )
        self.approved_patterns.append(
            CommandPattern(
                pattern=r"^echo\s+.*$",
                description="Echo text"
            )
        )
    
    def is_command_approved(self, command: str) -> bool:
        """Check if a command is approved and doesn't need confirmation.
        
        Args:
            command: The command to check.
            
        Returns:
            bool: True if the command is approved, False otherwise.
        """
        if not command or not command.strip():
            return False
            
        # Check if this is a piped command
        if self.parser.is_piped_command(command):
            # For piped commands, all parts must be approved
            sub_commands = self.parser.parse_command(command)
            return all(self._is_single_command_approved(cmd) for cmd in sub_commands)
        else:
            # For single commands, just check directly
            return self._is_single_command_approved(command)
    
    def _is_single_command_approved(self, command: str) -> bool:
        """Check if a single (non-piped) command is approved.
        
        Args:
            command: The command to check.
            
        Returns:
            bool: True if the command is approved, False otherwise.
        """
        command = command.strip()
        
        # Check exact matches first
        if command in self.approved_commands:
            return self.approved_commands[command]
            
        # Then check patterns
        for pattern in self.approved_patterns:
            if pattern.matches(command):
                return True
                
        return False
    
    def approve_command(self, command: str) -> None:
        """Add a command to the approved commands list.
        
        Args:
            command: The command to approve.
        """
        self.approved_commands[command] = True
        
        # In a real implementation, we would save this to config.toml
        logger.info(f"Command '{command}' approved for future use")

    async def handle_api_request(self, request: Request) -> Any:
        """Handles the incoming API request."""
        # This analyzer doesn't need to handle API requests
        return {'message': "Command approval analyzer doesn't support API requests"}

    async def security_risk(self, event: Action) -> ActionSecurityRisk:
        """Evaluates the Action for security risks and returns the risk level.

        For command approval analyzer, we always return LOW risk level,
        but we set the confirmation_state based on whether the command is approved.
        """
        # Only process CmdRunAction and IPythonRunCellAction
        if isinstance(event, CmdRunAction):
            command = event.command
            if self.is_command_approved(command):
                event.confirmation_state = ActionConfirmationStatus.CONFIRMED
                logger.info(f'Command automatically approved: {command}')

        elif isinstance(event, IPythonRunCellAction):
            code = event.code
            if self.is_command_approved(code):
                event.confirmation_state = ActionConfirmationStatus.CONFIRMED
                logger.info(f'Python code automatically approved: {code}')

        # Always return LOW risk level - we're not evaluating risk, just auto-approving
        return ActionSecurityRisk.LOW

    async def act(self, event: Event) -> None:
        """Performs an action based on the analyzed event.

        This analyzer doesn't need to perform any actions since command approval
        is handled directly in the CLI interface.
        """
        pass