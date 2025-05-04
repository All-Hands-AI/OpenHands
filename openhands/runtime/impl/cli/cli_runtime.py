"""
This runtime runs commands locally using subprocess and performs file operations using Python's standard library.
It does not implement browser functionality.
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, List, Optional, cast

from openhands.core.config import AppConfig
from openhands.core.exceptions import AgentRuntimeDisconnectedError
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.action import (
    Action,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.action.mcp import MCPAction
from openhands.events.observation import (
    AgentThinkObservation,
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.runtime.base import Runtime
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.utils.git_handler import CommandResult


class CLIRuntime(Runtime):
    """
    A runtime implementation that runs commands locally using subprocess and performs
    file operations using Python's standard library. It does not implement browser functionality.
    
    Args:
        config (AppConfig): The application configuration.
        event_stream (EventStream): The event stream to subscribe to.
        sid (str, optional): The session ID. Defaults to 'default'.
        plugins (list[PluginRequirement] | None, optional): List of plugin requirements. Defaults to None.
        env_vars (dict[str, str] | None, optional): Environment variables to set. Defaults to None.
        status_callback (Callable | None, optional): Callback for status updates. Defaults to None.
        attach_to_existing (bool, optional): Whether to attach to an existing session. Defaults to False.
        headless_mode (bool, optional): Whether to run in headless mode. Defaults to False.
        user_id (str | None, optional): User ID for authentication. Defaults to None.
        git_provider_tokens (PROVIDER_TOKEN_TYPE | None, optional): Git provider tokens. Defaults to None.
    """

    def __init__(
        self,
        config: AppConfig,
        event_stream: EventStream,
        sid: str = "default",
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable[[str, str, str], None] | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ):
        super().__init__(
            config,
            event_stream,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
            user_id,
            git_provider_tokens,
        )
        
        # Set up workspace
        if self.config.workspace_base is not None:
            logger.warning(
                f"Workspace base path is set to {self.config.workspace_base}. "
                "It will be used as the path for the agent to run in. "
                "Be careful, the agent can EDIT files in this directory!"
            )
            self._workspace_path = self.config.workspace_base
        else:
            # Create a temporary directory for the workspace
            self._workspace_path = tempfile.mkdtemp(prefix=f"openhands_workspace_{sid}_")
            logger.info(f"Created temporary workspace at {self._workspace_path}")
        
        # Initialize runtime state
        self._runtime_initialized = False
        
        logger.warning(
            "Initializing CLIRuntime. WARNING: NO SANDBOX IS USED. "
            "This runtime executes commands directly on the local system. "
            "Use with caution in untrusted environments."
        )

    async def connect(self) -> None:
        """Initialize the runtime connection."""
        self.send_status_message("STATUS$STARTING_RUNTIME")
        
        # Ensure workspace directory exists
        os.makedirs(self._workspace_path, exist_ok=True)
        
        # Change to the workspace directory
        os.chdir(self._workspace_path)
        
        if not self.attach_to_existing:
            await asyncio.to_thread(self.setup_initial_env)
        
        self._runtime_initialized = True
        self.send_status_message("STATUS$CONTAINER_STARTED")
        logger.info(f"CLIRuntime initialized with workspace at {self._workspace_path}")

    def _execute_shell_fn_git_handler(self, cmd: str) -> CommandResult:
        """Execute a shell command for the git handler."""
        return self._execute_shell_command(cmd)

    def _execute_shell_command(self, cmd: str) -> CommandResult:
        """Execute a shell command and return the result."""
        try:
            process = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._workspace_path,
            )
            return CommandResult(
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        except Exception as e:
            return CommandResult(
                exit_code=1,
                stdout="",
                stderr=f"Error executing command: {str(e)}",
            )

    def run(self, action: CmdRunAction) -> Observation:
        """Run a command using subprocess."""
        if not self._runtime_initialized:
            return ErrorObservation(f"Runtime not initialized: {action.command}")
        
        try:
            logger.debug(f"Running command: {action.command}")
            
            # Execute the command
            result = self._execute_shell_command(action.command)
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                if output:
                    output += "\n"
                output += result.stderr
            
            return CmdOutputObservation(
                content=output,
                exit_code=result.exit_code,
            )
        except Exception as e:
            logger.error(f"Error running command: {str(e)}")
            return ErrorObservation(f"Error running command: {str(e)}")

    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        """Run a Python code cell."""
        if not self._runtime_initialized:
            return ErrorObservation("Runtime not initialized")
        
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as temp_file:
            temp_file.write(action.code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the Python file
            result = self._execute_shell_command(f"python {temp_file_path}")
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                if output:
                    output += "\n"
                output += result.stderr
            
            return CmdOutputObservation(
                content=output,
                exit_code=result.exit_code,
            )
        except Exception as e:
            logger.error(f"Error running IPython cell: {str(e)}")
            return ErrorObservation(f"Error running IPython cell: {str(e)}")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

    def read(self, action: FileReadAction) -> Observation:
        """Read a file using Python's standard library."""
        if not self._runtime_initialized:
            return ErrorObservation("Runtime not initialized")
        
        file_path = os.path.join(self._workspace_path, action.path.lstrip("/"))
        
        try:
            # Check if the file exists
            if not os.path.exists(file_path):
                return ErrorObservation(f"File not found: {action.path}")
            
            # Check if it's a directory
            if os.path.isdir(file_path):
                return ErrorObservation(f"Cannot read directory: {action.path}")
            
            # Read the file
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            return FileReadObservation(content=content)
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return ErrorObservation(f"Error reading file {action.path}: {str(e)}")

    def write(self, action: FileWriteAction) -> Observation:
        """Write to a file using Python's standard library."""
        if not self._runtime_initialized:
            return ErrorObservation("Runtime not initialized")
        
        file_path = os.path.join(self._workspace_path, action.path.lstrip("/"))
        
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(action.content)
            
            return FileWriteObservation(success=True)
        except Exception as e:
            logger.error(f"Error writing to file: {str(e)}")
            return ErrorObservation(f"Error writing to file {action.path}: {str(e)}")

    def browse(self, action: BrowseURLAction) -> Observation:
        """Not implemented for CLI runtime."""
        return ErrorObservation("Browser functionality is not implemented in CLIRuntime")

    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        """Not implemented for CLI runtime."""
        return ErrorObservation("Browser functionality is not implemented in CLIRuntime")

    async def call_tool_mcp(self, action: MCPAction) -> Observation:
        """Not implemented for CLI runtime."""
        return ErrorObservation("MCP functionality is not implemented in CLIRuntime")

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        """Copy a file or directory from the host to the sandbox."""
        if not self._runtime_initialized:
            raise RuntimeError("Runtime not initialized")
        
        dest_path = os.path.join(self._workspace_path, sandbox_dest.lstrip("/"))
        
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            if recursive and os.path.isdir(host_src):
                # Copy directory recursively
                shutil.copytree(host_src, dest_path, dirs_exist_ok=True)
            else:
                # Copy file
                shutil.copy2(host_src, dest_path)
        except Exception as e:
            logger.error(f"Error copying file: {str(e)}")
            raise RuntimeError(f"Error copying file: {str(e)}")

    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox."""
        if not self._runtime_initialized:
            raise RuntimeError("Runtime not initialized")
        
        if path is None:
            dir_path = self._workspace_path
        else:
            dir_path = os.path.join(self._workspace_path, path.lstrip("/"))
        
        try:
            if not os.path.exists(dir_path):
                return []
            
            if not os.path.isdir(dir_path):
                return [dir_path]
            
            # List files in the directory
            return [os.path.join(dir_path, f) for f in os.listdir(dir_path)]
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []

    def copy_from(self, path: str) -> Path:
        """Zip all files in the sandbox and return a path in the local filesystem."""
        if not self._runtime_initialized:
            raise RuntimeError("Runtime not initialized")
        
        source_path = os.path.join(self._workspace_path, path.lstrip("/"))
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Path not found: {path}")
        
        # Create a temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temp_zip.close()
        
        try:
            with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isdir(source_path):
                    # Add all files in the directory
                    for root, _, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_path)
                            zipf.write(file_path, arcname)
                else:
                    # Add a single file
                    zipf.write(source_path, os.path.basename(source_path))
            
            return Path(temp_zip.name)
        except Exception as e:
            logger.error(f"Error creating zip file: {str(e)}")
            raise RuntimeError(f"Error creating zip file: {str(e)}")

    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, "_workspace_path") and self._workspace_path != self.config.workspace_base:
            try:
                shutil.rmtree(self._workspace_path)
                logger.info(f"Removed temporary workspace at {self._workspace_path}")
            except Exception as e:
                logger.error(f"Error removing temporary workspace: {str(e)}")
        
        self._runtime_initialized = False
        super().close()

    @classmethod
    async def delete(cls, conversation_id: str) -> None:
        """Delete any resources associated with a conversation."""
        # Look for temporary directories that might be associated with this conversation
        temp_dir = tempfile.gettempdir()
        prefix = f"openhands_workspace_{conversation_id}_"
        
        for item in os.listdir(temp_dir):
            if item.startswith(prefix):
                try:
                    path = os.path.join(temp_dir, item)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        logger.info(f"Deleted workspace directory: {path}")
                except Exception as e:
                    logger.error(f"Error deleting workspace directory: {str(e)}")

    def run_action(self, action: Action) -> Observation:
        """Run an action based on its type."""
        if isinstance(action, CmdRunAction):
            return self.run(action)
        elif isinstance(action, IPythonRunCellAction):
            return self.run_ipython(action)
        elif isinstance(action, FileReadAction):
            return self.read(action)
        elif isinstance(action, FileWriteAction):
            return self.write(action)
        elif isinstance(action, BrowseURLAction):
            return self.browse(action)
        elif isinstance(action, BrowseInteractiveAction):
            return self.browse_interactive(action)
        elif isinstance(action, MCPAction):
            return ErrorObservation("MCP functionality is not implemented in CLIRuntime")
        else:
            return ErrorObservation(f"Unsupported action type: {type(action).__name__}")