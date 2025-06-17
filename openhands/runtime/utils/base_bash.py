"""Base class for bash session implementations."""

from abc import ABC, abstractmethod

from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import CmdOutputObservation


class BashSession(ABC):
    """Abstract base class for bash session implementations."""

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        no_change_timeout_seconds: int = 30,
        max_memory_mb: int | None = None,
    ):
        """Initialize the bash session.

        Args:
            work_dir: Working directory for the session
            username: Username to run commands as
            no_change_timeout_seconds: Timeout for commands with no output changes
            max_memory_mb: Maximum memory limit in MB
        """
        self.work_dir = work_dir
        self.username = username
        self.no_change_timeout_seconds = no_change_timeout_seconds
        self.max_memory_mb = max_memory_mb
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the bash session."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the bash session and clean up resources."""
        pass

    @abstractmethod
    def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the bash session.

        Args:
            action: The command action to execute

        Returns:
            Observation containing the command output or error
        """
        pass

    @property
    @abstractmethod
    def cwd(self) -> str:
        """Get the current working directory.

        Returns:
            Current working directory path
        """
        pass

    @property
    def initialized(self) -> bool:
        """Check if the session is initialized."""
        return self._initialized
