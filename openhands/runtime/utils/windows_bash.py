"""
This module provides a Windows-specific implementation for running commands
in a PowerShell session using pythonnet to interact with the .NET
PowerShell SDK directly.
"""

import os
import time
import traceback
from pathlib import Path
from threading import RLock

import pythonnet

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import ErrorObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
)
from openhands.runtime.utils.bash_constants import TIMEOUT_MESSAGE_TEMPLATE
from openhands.runtime.utils.windows_exceptions import DotNetMissingError
from openhands.utils.shutdown_listener import should_continue

# -----------------------------
# Load CoreCLR / PythonNet
# -----------------------------
try:
    pythonnet.load('coreclr')
    import clr
except Exception as coreclr_ex:
    error_msg = 'Failed to load CoreCLR.'
    details = str(coreclr_ex)
    logger.error(f'{error_msg} Details: {details}')
    raise DotNetMissingError(error_msg, details)

# -----------------------------
# Load PowerShell SDK Assembly
# -----------------------------
ps_sdk_path = None
try:
    # Prioritize PowerShell 7+ if available
    pwsh7_path = Path(os.environ.get('ProgramFiles', 'C:\\Program Files')) / 'PowerShell' / '7' / 'System.Management.Automation.dll'
    if pwsh7_path.exists():
        ps_sdk_path = str(pwsh7_path)
        clr.AddReference(ps_sdk_path)
        logger.info(f'Loaded PowerShell SDK (Core): {ps_sdk_path}')
    else:
        # Fallback to Windows PowerShell 5.1
        winps_path = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'System.Management.Automation.dll'
        if winps_path.exists():
            ps_sdk_path = str(winps_path)
            clr.AddReference(ps_sdk_path)
            logger.debug(f'Loaded PowerShell SDK (Desktop): {ps_sdk_path}')
        else:
            # Last resort: load by assembly name
            clr.AddReference('System.Management.Automation')
            logger.info('Attempted to load PowerShell SDK by name (System.Management.Automation)')

    # Import PowerShell classes
    from System.Management.Automation import JobState, PowerShell
    from System.Management.Automation.Language import Parser
    from System.Management.Automation.Runspaces import RunspaceFactory, RunspaceState

except Exception as e:
    error_msg = 'Failed to load PowerShell SDK components.'
    details = f'{str(e)} (Path searched: {ps_sdk_path})'
    logger.error(f'{error_msg} Details: {details}')
    raise DotNetMissingError(error_msg, details)

# -----------------------------
# Windows PowerShell Session
# -----------------------------
class WindowsPowershellSession:
    """Manages a persistent PowerShell session using the .NET SDK via pythonnet."""

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        no_change_timeout_seconds: int = 30,
        max_memory_mb: int | None = None,
    ):
        self._closed = False
        self._initialized = False
        self.runspace = None

        if PowerShell is None:
            error_msg = 'PowerShell SDK could not be loaded.'
            logger.error(error_msg)
            raise DotNetMissingError(error_msg)

        self.work_dir = os.path.abspath(work_dir)
        self.no_change_timeout_seconds = no_change_timeout_seconds
        self.max_memory_mb = max_memory_mb

        self._lock = RLock()
        self._initialize_runspace()

    def _initialize_runspace(self):
        """Initialize the PowerShell runspace for this session."""
        try:
            self.runspace = RunspaceFactory.CreateRunspace()
            self.runspace.Open()
            self._initialized = True
            logger.info(f"PowerShell runspace initialized at {self.work_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize PowerShell runspace: {e}")
            raise

    def execute(self, command: str, timeout_seconds: int | None = None):
        """Execute a PowerShell command within the persistent session."""
        with self._lock:
            if self._closed or not self._initialized:
                raise RuntimeError("PowerShell session is not active.")

            ps_instance = PowerShell.Create()
            ps_instance.Runspace = self.runspace
            ps_instance.AddScript(command)

            timeout_seconds = timeout_seconds or self.no_change_timeout_seconds
            try:
                results = ps_instance.Invoke()
                errors = ps_instance.Streams.Error
                if errors.Count > 0:
                    for e in errors:
                        logger.error(f"PowerShell error: {e}")
                return results
            except Exception as ex:
                logger.error(f"Execution failed: {ex}")
                raise

    def close(self):
        """Close the PowerShell session."""
        with self._lock:
            if self._closed:
                return
            if self.runspace:
                try:
                    self.runspace.Close()
                except Exception as e:
                    logger.warning(f"Error closing runspace: {e}")
            self._closed = True
            logger.info("PowerShell session closed.")

    def __del__(self):
        self.close()
