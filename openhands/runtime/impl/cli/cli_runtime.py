"""This runtime runs commands locally using subprocess and performs file operations using Python's standard library.
It does not implement browser functionality.
"""

import asyncio
import os
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from binaryornot.check import is_binary

# Always define DotNetMissingError, even if import fails
try:
    from openhands.runtime.utils.windows_exceptions import DotNetMissingError
except ImportError:
    class DotNetMissingError(Exception):
        """Raised when .NET runtime or PowerShell SDK is missing."""
        pass

from openhands_aci.editor.editor import OHEditor
from openhands_aci.editor.exceptions import ToolError
from openhands_aci.editor.results import ToolResult
from openhands_aci.utils.diff import get_diff
from pydantic import SecretStr

from openhands.core.config import OpenHandsConfig
from openhands.core.config.mcp_config import MCPConfig, MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import (
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.action.mcp import MCPAction
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime_status import RuntimeStatus

if TYPE_CHECKING:
    from openhands.runtime.utils.windows_bash import WindowsPowershellSession

# Import Windows PowerShell support if on Windows
if sys.platform == 'win32':
    try:
        from openhands.runtime.utils.windows_bash import WindowsPowershellSession
    except ImportError as err:

        ...
        # Print a user-friendly error message without stack trace
        friendly_message = """
ERROR: PowerShell and .NET SDK are required but not properly configured

The .NET SDK and PowerShell are required for OpenHands CLI on Windows.
PowerShell integration cannot function without .NET Core.

Please install the .NET SDK by following the instructions at:
https://docs.all-hands.dev/usage/windows-without-wsl

After installing .NET SDK, restart your terminal and try again.
"""
        print(friendly_message, file=sys.stderr)
        logger.error(
            f'Windows runtime initialization failed: {type(err).__name__}: {str(err)}'
        )
        if (
            isinstance(err, DotNetMissingError)
            and hasattr(err, 'details')
            and err.details
        ):
            logger.debug(f'Details: {err.details}')

        # Exit the program with an error code
        sys.exit(1)

# (The rest of the file remains unchanged from your original)
