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
from typing import Callable, Optional, Tuple

from binaryornot.check import is_binary
from openhands_aci.editor.editor import OHEditor
from openhands_aci.editor.exceptions import ToolError
from openhands_aci.editor.results import ToolResult
from openhands_aci.utils.diff import get_diff

from openhands.core.config import AppConfig
from openhands.core.config.mcp_config import MCPConfig
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
        sid: str = 'default',
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
                f'Workspace base path is set to {self.config.workspace_base}. '
                'It will be used as the path for the agent to run in. '
                'Be careful, the agent can EDIT files in this directory!'
            )
            self._workspace_path = self.config.workspace_base
        else:
            # Create a temporary directory for the workspace
            self._workspace_path = tempfile.mkdtemp(
                prefix=f'openhands_workspace_{sid}_'
            )
            logger.info(f'Created temporary workspace at {self._workspace_path}')

        # Initialize runtime state
        self._runtime_initialized = False
        self.file_editor = OHEditor(workspace_root=self._workspace_path)
        self._shell_stream_callback: Optional[Callable[[str], None]] = None

        logger.warning(
            'Initializing CLIRuntime. WARNING: NO SANDBOX IS USED. '
            'This runtime executes commands directly on the local system. '
            'Use with caution in untrusted environments.'
        )

    async def connect(self) -> None:
        """Initialize the runtime connection."""
        self.send_status_message('STATUS$STARTING_RUNTIME')

        # Ensure workspace directory exists
        os.makedirs(self._workspace_path, exist_ok=True)

        # Change to the workspace directory
        os.chdir(self._workspace_path)

        if not self.attach_to_existing:
            await asyncio.to_thread(self.setup_initial_env)

        self._runtime_initialized = True
        self.send_status_message('STATUS$CONTAINER_STARTED')
        logger.info(f'CLIRuntime initialized with workspace at {self._workspace_path}')

    def _execute_shell_command(self, command: str) -> CmdOutputObservation:
        """
        Execute a shell command and stream its output to a callback function.
        Args:
            command: The shell command to execute
        Returns:
            CmdOutputObservation containing the complete output and exit code
        """
        full_output = []

        # Use shell=True to run complex bash commands
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout for interleaved output
            text=True,
            bufsize=0,  # Unbuffered output
            universal_newlines=True,
            shell=True,  # Run through a shell
        )

        while process.poll() is None:
            if not process.stdout:
                continue
            output = process.stdout.readline()
            if output:
                full_output.append(output)
                if self._shell_stream_callback:
                    self._shell_stream_callback(output)

        # Make sure we get any remaining output after process exits
        remaining_output, _ = process.communicate()
        if remaining_output:
            full_output.append(remaining_output)
            if self._shell_stream_callback:
                self._shell_stream_callback(remaining_output)

        exit_code = process.returncode

        complete_output = ''.join(full_output)

        return CmdOutputObservation(
            command=command,
            content=complete_output,
            exit_code=exit_code,
        )

    def run(self, action: CmdRunAction) -> Observation:
        """Run a command using subprocess."""
        if not self._runtime_initialized:
            return ErrorObservation(f'Runtime not initialized: {action.command}')

        try:
            logger.debug(f'Running command: {action.command}')

            # Execute the command and return the CmdOutputObservation
            return self._execute_shell_command(action.command)
        except Exception as e:
            logger.error(f'Error running command: {str(e)}')
            return ErrorObservation(f'Error running command: {str(e)}')

    def run_ipython(self, action: IPythonRunCellAction) -> Observation:
        """Run a Python code cell."""
        if not self._runtime_initialized:
            return ErrorObservation('Runtime not initialized')

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(
            suffix='.py', mode='w', delete=False
        ) as temp_file:
            temp_file.write(action.code)
            temp_file_path = temp_file.name

        try:
            return self._execute_shell_command(f'python {temp_file_path}')
        except Exception as e:
            logger.error(f'Error running IPython cell: {str(e)}')
            return ErrorObservation(f'Error running IPython cell: {str(e)}')
        finally:
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

    def _sanitize_filename(self, filename: str) -> str:
        # if path is absolute, ensure it starts with _workspace_path
        if filename.startswith('/'):
            if not filename.startswith(self._workspace_path):
                raise ValueError(
                    f'Invalid path: {filename}. You can only work with files in {self._workspace_path}.'
                )
        else:
            filename = os.path.join(self._workspace_path, filename.lstrip('/'))
        return filename

    def read(self, action: FileReadAction) -> Observation:
        """Read a file using Python's standard library or OHEditor."""
        if not self._runtime_initialized:
            return ErrorObservation('Runtime not initialized')

        file_path = self._sanitize_filename(action.path)

        # Cannot read binary files
        if os.path.exists(file_path) and is_binary(file_path):
            return ErrorObservation('ERROR_BINARY_FILE')

        # Use OHEditor for OH_ACI implementation source
        if action.impl_source == FileReadSource.OH_ACI:
            result_str, _ = self._execute_file_editor(
                command='view',
                path=file_path,
                view_range=action.view_range,
            )

            return FileReadObservation(
                content=result_str,
                path=action.path,
                impl_source=FileReadSource.OH_ACI,
            )

        try:
            # Check if the file exists
            if not os.path.exists(file_path):
                return ErrorObservation(f'File not found: {action.path}')

            # Check if it's a directory
            if os.path.isdir(file_path):
                return ErrorObservation(f'Cannot read directory: {action.path}')

            # Read the file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return FileReadObservation(content=content, path=action.path)
        except Exception as e:
            logger.error(f'Error reading file: {str(e)}')
            return ErrorObservation(f'Error reading file {action.path}: {str(e)}')

    def write(self, action: FileWriteAction) -> Observation:
        """Write to a file using Python's standard library."""
        if not self._runtime_initialized:
            return ErrorObservation('Runtime not initialized')

        file_path = self._sanitize_filename(action.path)

        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(action.content)

            return FileWriteObservation(content='', path=action.path)
        except Exception as e:
            logger.error(f'Error writing to file: {str(e)}')
            return ErrorObservation(f'Error writing to file {action.path}: {str(e)}')

    def browse(self, action: BrowseURLAction) -> Observation:
        """Not implemented for CLI runtime."""
        return ErrorObservation(
            'Browser functionality is not implemented in CLIRuntime'
        )

    def browse_interactive(self, action: BrowseInteractiveAction) -> Observation:
        """Not implemented for CLI runtime."""
        return ErrorObservation(
            'Browser functionality is not implemented in CLIRuntime'
        )

    def _execute_file_editor(
        self,
        command: str,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        enable_linting: bool = False,
    ) -> Tuple[str, Tuple[str | None, str | None]]:
        """Execute file editor command and handle exceptions.

        Args:
            command: Editor command to execute
            path: File path
            file_text: Optional file text content
            view_range: Optional view range tuple (start, end)
            old_str: Optional string to replace
            new_str: Optional replacement string
            insert_line: Optional line number for insertion
            enable_linting: Whether to enable linting

        Returns:
            tuple: A tuple containing the output string and a tuple of old and new file content
        """
        result: ToolResult | None = None
        try:
            result = self.file_editor(
                command=command,
                path=path,
                file_text=file_text,
                view_range=view_range,
                old_str=old_str,
                new_str=new_str,
                insert_line=insert_line,
                enable_linting=enable_linting,
            )
        except ToolError as e:
            result = ToolResult(error=e.message)

        if result.error:
            return f'ERROR:\n{result.error}', (None, None)

        if not result.output:
            logger.warning(f'No output from file_editor for {path}')
            return '', (None, None)

        return result.output, (result.old_content, result.new_content)

    def edit(self, action: FileEditAction) -> Observation:
        """Edit a file using the OHEditor."""
        if not self._runtime_initialized:
            return ErrorObservation('Runtime not initialized')

        # Ensure the path is within the workspace
        file_path = self._sanitize_filename(action.path)

        # Check if it's a binary file
        if os.path.exists(file_path) and is_binary(file_path):
            return ErrorObservation('ERROR_BINARY_FILE')

        assert action.impl_source == FileEditSource.OH_ACI

        result_str, (old_content, new_content) = self._execute_file_editor(
            command=action.command,
            path=file_path,
            file_text=action.file_text,
            old_str=action.old_str,
            new_str=action.new_str,
            insert_line=action.insert_line,
            enable_linting=False,
        )

        return FileEditObservation(
            content=result_str,
            path=action.path,
            old_content=action.old_str,
            new_content=action.new_str,
            impl_source=FileEditSource.OH_ACI,
            diff=get_diff(
                old_contents=old_content or '',
                new_contents=new_content or '',
                filepath=action.path,
            ),
        )

    async def call_tool_mcp(self, action: MCPAction) -> Observation:
        """Not implemented for CLI runtime."""
        return ErrorObservation('MCP functionality is not implemented in CLIRuntime')

    @property
    def workspace_root(self) -> Path:
        """Return the workspace root path."""
        return Path(os.path.abspath(self._workspace_path))

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        """Copy a file or directory from the host to the sandbox."""
        if not self._runtime_initialized:
            raise RuntimeError('Runtime not initialized')

        dest_path = os.path.join(self._workspace_path, sandbox_dest.lstrip('/'))

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
            logger.error(f'Error copying file: {str(e)}')
            raise RuntimeError(f'Error copying file: {str(e)}')

    def list_files(self, path: str | None = None) -> list[str]:
        """List files in the sandbox."""
        if not self._runtime_initialized:
            raise RuntimeError('Runtime not initialized')

        if path is None:
            dir_path = self._workspace_path
        else:
            dir_path = self._sanitize_filename(path)

        try:
            if not os.path.exists(dir_path):
                return []

            if not os.path.isdir(dir_path):
                return [dir_path]

            # List files in the directory
            return [os.path.join(dir_path, f) for f in os.listdir(dir_path)]
        except Exception as e:
            logger.error(f'Error listing files: {str(e)}')
            return []

    def copy_from(self, path: str) -> Path:
        """Zip all files in the sandbox and return a path in the local filesystem."""
        if not self._runtime_initialized:
            raise RuntimeError('Runtime not initialized')

        source_path = self._sanitize_filename(path)

        if not os.path.exists(source_path):
            raise FileNotFoundError(f'Path not found: {path}')

        # Create a temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        temp_zip.close()

        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
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
            logger.error(f'Error creating zip file: {str(e)}')
            raise RuntimeError(f'Error creating zip file: {str(e)}')

    def close(self) -> None:
        self._runtime_initialized = False
        super().close()

    @classmethod
    async def delete(cls, conversation_id: str) -> None:
        """Delete any resources associated with a conversation."""
        # Look for temporary directories that might be associated with this conversation
        temp_dir = tempfile.gettempdir()
        prefix = f'openhands_workspace_{conversation_id}_'

        for item in os.listdir(temp_dir):
            if item.startswith(prefix):
                try:
                    path = os.path.join(temp_dir, item)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        logger.info(f'Deleted workspace directory: {path}')
                except Exception as e:
                    logger.error(f'Error deleting workspace directory: {str(e)}')

    @property
    def additional_agent_instructions(self) -> str:
        return '\n\n'.join(
            [
                f'Your working directory is {self._workspace_path}. You can only read and write files in this directory.',
                "You are working directly on the user's machine. In most cases, the working environment is already set up.",
            ]
        )

    def get_mcp_config(self) -> MCPConfig:
        # TODO: Load MCP config from a local file
        return MCPConfig()

    def subscribe_to_shell_stream(
        self, callback: Callable[[str], None] | None = None
    ) -> bool:
        """
        Subscribe to shell command output stream.

        Args:
            callback: A function that will be called with each line of output from shell commands.
                     If None, any existing subscription will be removed.
        """
        self._shell_stream_callback = callback
        return True
