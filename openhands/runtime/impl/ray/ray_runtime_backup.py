"""Ray Runtime implementation for distributed OpenHands execution."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

import ray

from openhands.core.config import OpenHandsConfig
from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.runtime.plugins import PluginRequirement
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.runtime.utils.command import (
    DEFAULT_MAIN_MODULE,
    get_action_execution_server_startup_command,
)
from openhands.utils.tenacity_stop import stop_if_should_exit

from .worker_pool import RayWorkerPool, WorkerSelectionStrategy
from .session_manager import SessionManager, SessionType
from .ray_actor import RayExecutionActor
class RayExecutionActor:
    """Ray actor for executing commands in an isolated environment."""
    
    def __init__(self, workspace_path: str, env_vars: dict[str, str]):
        """Initialize the Ray execution actor.
        
        Args:
            workspace_path: Path to the workspace directory
            env_vars: Environment variables to set
        """
        self.workspace_path = workspace_path
        self.env_vars = env_vars
        self.current_dir = workspace_path
        
        # Ensure workspace directory exists
        os.makedirs(workspace_path, exist_ok=True)
        
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
            
        logger.info(f"Ray actor initialized with workspace: {workspace_path}")
    
    async def execute_command(self, command: str, timeout: int = 60) -> dict[str, Any]:
        """Execute a shell command and return the result.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict containing exit_code, stdout, stderr
        """
        import subprocess
        import asyncio
        
        try:
            # Change to current directory for execution
            os.chdir(self.current_dir)
            
            # Execute command with asyncio subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.current_dir,
                env={**os.environ, **self.env_vars}
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                exit_code = process.returncode
                
                return {
                    'exit_code': exit_code,
                    'stdout': stdout.decode('utf-8', errors='replace'),
                    'stderr': stderr.decode('utf-8', errors='replace'),
                }
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    'exit_code': 124,  # Standard timeout exit code
                    'stdout': '',
                    'stderr': f'Command timed out after {timeout} seconds',
                }
                
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
            }
    
    async def read_file(self, file_path: str) -> dict[str, Any]:
        """Read a file and return its contents.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Dict containing success status and content or error message
        """
        try:
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.workspace_path, file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'success': True,
                'content': content,
            }
        except Exception as e:
            logger.error(f"Error reading file '{file_path}': {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def write_file(self, file_path: str, content: str) -> dict[str, Any]:
        """Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Returns:
            Dict containing success status
        """
        try:
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.workspace_path, file_path)
            
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
            }
        except Exception as e:
            logger.error(f"Error writing file '{file_path}': {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def change_directory(self, path: str) -> dict[str, Any]:
        """Change the current working directory.
        
        Args:
            path: Directory to change to
            
        Returns:
            Dict containing success status and current directory
        """
        try:
            # Convert to absolute path if relative
            if not os.path.isabs(path):
                path = os.path.join(self.workspace_path, path)
            
            if os.path.exists(path) and os.path.isdir(path):
                self.current_dir = path
                os.chdir(path)
                return {
                    'success': True,
                    'current_dir': self.current_dir,
                }
            else:
                return {
                    'success': False,
                    'error': f"Directory does not exist: {path}",
                }
        except Exception as e:
            logger.error(f"Error changing directory to '{path}': {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def edit_file(self, file_path: str, new_str: str, old_str: str = None, start_line: int = None, end_line: int = None) -> dict[str, Any]:
        """Edit a file with string replacement or line-based editing.
        
        Args:
            file_path: Path to the file to edit
            new_str: New content to insert/replace
            old_str: Old content to replace (for string-based editing)
            start_line: Start line for line-based editing (1-indexed)
            end_line: End line for line-based editing (1-indexed)
            
        Returns:
            Dict containing success status and updated content
        """
        try:
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.workspace_path, file_path)
            
            # Read current file content
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = ''
            
            # Perform edit operation
            if old_str is not None:
                # String-based replacement
                if old_str in content:
                    new_content = content.replace(old_str, new_str)
                else:
                    return {
                        'success': False,
                        'error': f'String "{old_str}" not found in file',
                    }
            elif start_line is not None:
                # Line-based editing
                lines = content.splitlines(keepends=True)
                start_idx = start_line - 1  # Convert to 0-indexed
                end_idx = end_line if end_line else start_line
                end_idx = min(end_idx, len(lines))  # Ensure we don't exceed file length
                
                # Replace lines
                new_lines = new_str.splitlines(keepends=True)
                lines[start_idx:end_idx] = new_lines
                new_content = ''.join(lines)
            else:
                # Full file replacement
                new_content = new_str
            
            # Write updated content
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                'success': True,
                'content': new_content,
            }
            
        except Exception as e:
            logger.error(f"Error editing file '{file_path}': {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def run_ipython(self, code: str, kernel_init_code: str = None) -> dict[str, Any]:
        """Execute IPython/Jupyter code.
        
        Args:
            code: Python code to execute
            kernel_init_code: Optional initialization code
            
        Returns:
            Dict containing execution result
        """
        try:
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            
            # Capture output
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            # Create a clean execution environment
            exec_globals = {
                '__name__': '__main__',
                '__builtins__': __builtins__,
            }
            
            # Add current working directory to Python path
            if self.current_dir not in sys.path:
                sys.path.insert(0, self.current_dir)
            
            # Execute initialization code if provided
            if kernel_init_code:
                with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                    exec(kernel_init_code, exec_globals)
            
            # Execute the main code
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                try:
                    # Try to evaluate as expression first
                    result = eval(code, exec_globals)
                    if result is not None:
                        stdout_buffer.write(repr(result))
                except SyntaxError:
                    # If it fails as expression, execute as statement
                    exec(code, exec_globals)
            
            # Get output
            stdout_content = stdout_buffer.getvalue()
            stderr_content = stderr_buffer.getvalue()
            
            # Combine output
            output = stdout_content
            if stderr_content:
                output += '\n' + stderr_content
            
            return {
                'success': True,
                'content': output,
            }
            
        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            logger.error(f"IPython execution error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
            }
    
    async def browse_url(self, url: str) -> dict[str, Any]:
        """Browse a URL and return content.
        
        Args:
            url: URL to browse
            
        Returns:
            Dict containing page content
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type:
                    # For HTML content, try to extract readable text
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        content = soup.get_text(separator='\n', strip=True)
                    except ImportError:
                        # Fallback to raw HTML if beautifulsoup is not available
                        content = response.text[:10000]  # Limit content length
                else:
                    content = response.text[:10000]  # Limit content length
            
            return {
                'success': True,
                'content': content,
                'url': url,
            }
            
        except Exception as e:
            logger.error(f"Error browsing URL '{url}': {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def browse_interactive(self, browser_actions: list) -> dict[str, Any]:
        """Perform interactive browser actions.
        
        Args:
            browser_actions: List of browser actions to perform
            
        Returns:
            Dict containing interaction result
        """
        try:
            # This is a simplified implementation
            # In a full implementation, you would integrate with a browser automation library
            # like Selenium or Playwright
            
            result_content = "Interactive browsing not fully implemented in Ray actor yet.\n"
            result_content += f"Requested actions: {browser_actions}"
            
            return {
                'success': True,
                'content': result_content,
                'url': 'about:blank',
            }
            
        except Exception as e:
            logger.error(f"Error with interactive browsing: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def ping(self) -> dict[str, Any]:
        """Health check method for worker pool monitoring."""
        import time
        return {
            'success': True,
            'timestamp': time.time(),
            'workspace_path': self.workspace_path,
        }


class RayRuntime(ActionExecutionClient):
    """Ray-based runtime for distributed OpenHands execution.
    
    This runtime uses Ray actors to execute commands in a distributed manner,
    allowing for horizontal scaling across a Ray cluster.
    """
    
    def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        llm_registry: LLMRegistry,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = True,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
        main_module: str = DEFAULT_MAIN_MODULE,
    ):
        """Initialize the Ray runtime.
        
        Args:
            config: OpenHands configuration
            event_stream: Event stream for communication
            llm_registry: LLM registry
            sid: Session ID
            plugins: List of plugin requirements
            env_vars: Environment variables
            status_callback: Status callback function
            attach_to_existing: Whether to attach to existing runtime
            headless_mode: Whether to run in headless mode
            user_id: User ID
            git_provider_tokens: Git provider tokens
            main_module: Main module to run
        """
        self.config = config
        self.status_callback = status_callback
        self.main_module = main_module
        
        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            try:
                ray.init(
                    address=config.sandbox.ray_cluster_address if hasattr(config.sandbox, 'ray_cluster_address') else None,
                    ignore_reinit_error=True
                )
                logger.info("Ray initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Ray: {e}")
                raise AgentRuntimeError(f"Ray initialization failed: {e}")
        
        # Create workspace directory
        self.workspace_path = os.path.join(
            tempfile.gettempdir(), 
            f"openhands-ray-workspace-{sid}-{uuid4().hex[:8]}"
        )
        os.makedirs(self.workspace_path, exist_ok=True)
        
        # Prepare environment variables
        self._env_vars = env_vars or {}
        self._env_vars.update({
            'OPENHANDS_SESSION_ID': sid,
            'OPENHANDS_WORKSPACE_PATH': self.workspace_path,
        })
        
        # Create worker pool and session manager
        pool_size = getattr(config.sandbox, 'ray_worker_pool_size', 3)
        max_pool_size = getattr(config.sandbox, 'ray_max_pool_size', 10)
        selection_strategy = getattr(config.sandbox, 'ray_selection_strategy', 'least_busy')
        
        strategy_map = {
            'round_robin': WorkerSelectionStrategy.ROUND_ROBIN,
            'least_busy': WorkerSelectionStrategy.LEAST_BUSY,
            'random': WorkerSelectionStrategy.RANDOM,
            'session_affinity': WorkerSelectionStrategy.SESSION_AFFINITY,
        }
        
        self.worker_pool = RayWorkerPool(
            pool_size=pool_size,
            max_pool_size=max_pool_size,
            selection_strategy=strategy_map.get(selection_strategy, WorkerSelectionStrategy.LEAST_BUSY)
        )
        
        self.session_manager = SessionManager()
        self.session_id = sid
        
        # Create session for this runtime instance
        self.session_manager.create_session(
            session_type=SessionType.COMBINED,
            session_id=self.session_id
        )
        
        # Legacy compatibility: maintain reference for backward compatibility
        # This will be deprecated once all methods use worker pool
        self.actor = None
        
        logger.info(f"RayRuntime initialized for session {sid}")
        logger.info(f"Workspace path: {self.workspace_path}")
        
        # Call parent constructor
        super().__init__(
            config,
            event_stream,
            llm_registry,
            sid,
            plugins,
            env_vars,
            status_callback,
            attach_to_existing,
            headless_mode,
            user_id,
            git_provider_tokens,
        )
    
    async def connect(self) -> None:
        """Connect to the Ray runtime."""
        try:
            # Initialize worker pool and session manager
            await self.worker_pool.initialize()
            await self.session_manager.initialize()
            
            # Test that the worker pool is responsive with a simple action
            test_action_data = {
                'type': 'CmdRunAction',
                'command': "echo 'Ray runtime connected'",
                'timeout': 30
            }
            result = await self.worker_pool.execute_action(test_action_data, self.session_id)
            
            if result.get('exit_code') == 0:
                logger.info("Ray runtime connected successfully")
                self._runtime_initialized = True
                if self.status_callback:
                    self.status_callback('info', RuntimeStatus.RUNNING, 'Ray runtime connected')
            else:
                raise AgentRuntimeError(f"Ray worker pool connection test failed: {result}")
                
        except Exception as e:
            logger.error(f"Failed to connect to Ray runtime: {e}")
            if self.status_callback:
                self.status_callback('error', RuntimeStatus.ERROR, f'Ray connection failed: {e}')
            raise AgentRuntimeDisconnectedError(f"Ray runtime connection failed: {e}")
    
    def close(self) -> None:
        """Close the Ray runtime and cleanup resources."""
        try:
            # Shutdown worker pool and session manager
            if hasattr(self, 'worker_pool'):
                asyncio.get_event_loop().run_until_complete(self.worker_pool.shutdown())
                logger.info("Ray worker pool terminated")
            
            if hasattr(self, 'session_manager'):
                asyncio.get_event_loop().run_until_complete(self.session_manager.shutdown())
                logger.info("Session manager terminated")
            
            # Legacy cleanup for backward compatibility
            if hasattr(self, 'actor') and self.actor:
                ray.kill(self.actor)
                logger.info("Ray actor terminated")
            
            # Cleanup workspace directory
            if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
                import shutil
                shutil.rmtree(self.workspace_path, ignore_errors=True)
                logger.info(f"Workspace directory cleaned up: {self.workspace_path}")
                
        except Exception as e:
            logger.error(f"Error closing Ray runtime: {e}")
        
        super().close()
    
    @property
    def api_url(self) -> str:
        """Return the API URL for the runtime."""
        # Ray runtime doesn't use HTTP API, return a placeholder
        return f"ray://workspace/{self.workspace_path}"
    
    @property
    def workspace_root(self) -> Path:
        """Return the workspace root path."""
        return Path(self.workspace_path)
    
    def get_working_directory(self) -> str:
        """Get the current working directory."""
        return self.workspace_path
    
    async def _execute_command(self, command: str, timeout: int = 60) -> dict[str, Any]:
        """Execute a command using the Ray worker pool.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict containing execution result
        """
        try:
            action_data = {
                'type': 'CmdRunAction',
                'command': command,
                'timeout': timeout
            }
            result = await self.worker_pool.execute_action(action_data, self.session_id, timeout)
            return result
        except Exception as e:
            logger.error(f"Error executing command via Ray: {e}")
            return {
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
            }
    
    async def _read_file(self, file_path: str) -> dict[str, Any]:
        """Read a file using the Ray worker pool.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Dict containing file contents or error
        """
        try:
            action_data = {
                'type': 'FileReadAction',
                'path': file_path
            }
            result = await self.worker_pool.execute_action(action_data, self.session_id)
            return result
        except Exception as e:
            logger.error(f"Error reading file via Ray: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def _write_file(self, file_path: str, content: str) -> dict[str, Any]:
        """Write a file using the Ray worker pool.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Returns:
            Dict containing success status
        """
        try:
            action_data = {
                'type': 'FileWriteAction',
                'path': file_path,
                'content': content
            }
            result = await self.worker_pool.execute_action(action_data, self.session_id)
            return result
        except Exception as e:
            logger.error(f"Error writing file via Ray: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _run_async_action(self, action_data: dict, session_id: Optional[str] = None, timeout: Optional[float] = None) -> dict:
        """Helper to run async worker pool actions synchronously."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.worker_pool.execute_action(action_data, session_id or self.session_id, timeout)
        )
    
    # Override ActionExecutionClient methods to use Ray worker pool instead of HTTP
    
    def run(self, action) -> 'Observation':
        """Execute a CmdRunAction using Ray worker pool."""
        from openhands.events.observation import CmdOutputObservation, ErrorObservation
        
        try:
            # Execute command via Ray worker pool
            action_data = {
                'type': 'CmdRunAction',
                'command': action.command,
                'timeout': action.timeout or 60
            }
            
            result = self._run_async_action(action_data, timeout=action.timeout or 60)
            
            # Convert Ray result to CmdOutputObservation
            return CmdOutputObservation(
                content=result.get('stdout', ''),
                exit_code=result.get('exit_code', 1),
                command=action.command,
                command_id=action.id,
            )
        except Exception as e:
            logger.error(f"Error executing command action via Ray: {e}")
            return ErrorObservation(
                f"Ray execution failed: {str(e)}",
                error_id='RAY_EXECUTION_ERROR'
            )
    
    def read(self, action) -> 'Observation':
        """Execute a FileReadAction using Ray worker pool."""
        from openhands.events.observation import FileReadObservation, ErrorObservation
        
        try:
            # Read file via Ray worker pool
            action_data = {
                'type': 'FileReadAction',
                'path': action.path
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return FileReadObservation(
                    content=result.get('content', ''),
                    path=action.path,
                )
            else:
                return ErrorObservation(
                    f"Failed to read file: {result.get('error', 'Unknown error')}",
                    error_id='FILE_READ_ERROR'
                )
        except Exception as e:
            logger.error(f"Error reading file via Ray: {e}")
            return ErrorObservation(
                f"Ray file read failed: {str(e)}",
                error_id='RAY_FILE_READ_ERROR'
            )
    
    def write(self, action) -> 'Observation':
        """Execute a FileWriteAction using Ray worker pool."""
        from openhands.events.observation import FileWriteObservation, ErrorObservation
        
        try:
            # Write file via Ray worker pool
            action_data = {
                'type': 'FileWriteAction',
                'path': action.path,
                'content': action.content
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return FileWriteObservation(
                    content=action.content,
                    path=action.path,
                )
            else:
                return ErrorObservation(
                    f"Failed to write file: {result.get('error', 'Unknown error')}",
                    error_id='FILE_WRITE_ERROR'
                )
        except Exception as e:
            logger.error(f"Error writing file via Ray: {e}")
            return ErrorObservation(
                f"Ray file write failed: {str(e)}",
                error_id='RAY_FILE_WRITE_ERROR'
            )
    
    def edit(self, action) -> 'Observation':
        """Execute a FileEditAction using Ray actor."""
        from openhands.events.observation import FileEditObservation, ErrorObservation
        
        try:
            # Use Ray worker pool to perform file edit
            action_data = {
                'type': 'FileEditAction',
                'path': action.path,
                'new_str': action.new_str,
                'old_str': getattr(action, 'old_str', None),
                'start_line': getattr(action, 'start_line', None),
                'end_line': getattr(action, 'end_line', None)
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return FileEditObservation(
                    content=result.get('content', ''),
                    path=action.path,
                )
            else:
                return ErrorObservation(
                    f"Failed to edit file: {result.get('error', 'Unknown error')}",
                    error_id='FILE_EDIT_ERROR'
                )
        except Exception as e:
            logger.error(f"Error editing file via Ray: {e}")
            return ErrorObservation(
                f"Ray file edit failed: {str(e)}",
                error_id='RAY_FILE_EDIT_ERROR'
            )
    
    def run_ipython(self, action) -> 'Observation':
        """Execute an IPythonRunCellAction using Ray actor."""
        from openhands.events.observation import IPythonRunCellObservation, ErrorObservation
        
        try:
            # Execute IPython code via Ray worker pool (using session affinity for kernel state)
            action_data = {
                'type': 'IPythonRunCellAction',
                'code': action.code,
                'kernel_init_code': getattr(action, 'kernel_init_code', None)
            }
            
            result = self._run_async_action(action_data)
            
            if result.get('success', False):
                return IPythonRunCellObservation(
                    content=result.get('content', ''),
                    code=action.code,
                )
            else:
                return ErrorObservation(
                    f"Failed to run IPython code: {result.get('error', 'Unknown error')}",
                    error_id='IPYTHON_EXECUTION_ERROR'
                )
        except Exception as e:
            logger.error(f"Error executing IPython code via Ray: {e}")
            return ErrorObservation(
                f"Ray IPython execution failed: {str(e)}",
                error_id='RAY_IPYTHON_ERROR'
            )
    
    def browse(self, action) -> 'Observation':
        """Execute a BrowseURLAction using Ray actor."""
        from openhands.events.observation import BrowserOutputObservation, ErrorObservation
        
        try:
            # Browse URL via Ray actor
            future = self.actor.browse_url.remote(action.url)
            result = ray.get(future)
            
            if result.get('success', False):
                return BrowserOutputObservation(
                    content=result.get('content', ''),
                    url=action.url,
                    screenshot=result.get('screenshot'),
                )
            else:
                return ErrorObservation(
                    f"Failed to browse URL: {result.get('error', 'Unknown error')}",
                    error_id='BROWSER_ERROR'
                )
        except Exception as e:
            logger.error(f"Error browsing URL via Ray: {e}")
            return ErrorObservation(
                f"Ray browser failed: {str(e)}",
                error_id='RAY_BROWSER_ERROR'
            )
    
    def browse_interactive(self, action) -> 'Observation':
        """Execute a BrowseInteractiveAction using Ray actor."""
        from openhands.events.observation import BrowserOutputObservation, ErrorObservation
        
        try:
            # Interactive browse via Ray actor
            future = self.actor.browse_interactive.remote(
                action.browser_actions if hasattr(action, 'browser_actions') else []
            )
            result = ray.get(future)
            
            if result.get('success', False):
                return BrowserOutputObservation(
                    content=result.get('content', ''),
                    url=result.get('url', ''),
                    screenshot=result.get('screenshot'),
                )
            else:
                return ErrorObservation(
                    f"Failed to perform interactive browsing: {result.get('error', 'Unknown error')}",
                    error_id='INTERACTIVE_BROWSER_ERROR'
                )
        except Exception as e:
            logger.error(f"Error with interactive browsing via Ray: {e}")
            return ErrorObservation(
                f"Ray interactive browser failed: {str(e)}",
                error_id='RAY_INTERACTIVE_BROWSER_ERROR'
            )