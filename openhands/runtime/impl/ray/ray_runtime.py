"""Ray Runtime implementation for distributed OpenHands execution."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable
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


@ray.remote
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
        
        # Create Ray actor
        self.actor = RayExecutionActor.remote(
            workspace_path=self.workspace_path,
            env_vars=self._env_vars
        )
        
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
            # Test that the actor is responsive
            future = self.actor.execute_command.remote("echo 'Ray runtime connected'")
            result = ray.get(future)
            
            if result['exit_code'] == 0:
                logger.info("Ray runtime connected successfully")
                self._runtime_initialized = True
                if self.status_callback:
                    self.status_callback('info', RuntimeStatus.RUNNING, 'Ray runtime connected')
            else:
                raise AgentRuntimeError(f"Ray actor connection test failed: {result}")
                
        except Exception as e:
            logger.error(f"Failed to connect to Ray runtime: {e}")
            if self.status_callback:
                self.status_callback('error', RuntimeStatus.ERROR, f'Ray connection failed: {e}')
            raise AgentRuntimeDisconnectedError(f"Ray runtime connection failed: {e}")
    
    def close(self) -> None:
        """Close the Ray runtime and cleanup resources."""
        try:
            if hasattr(self, 'actor'):
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
        """Execute a command using the Ray actor.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict containing execution result
        """
        try:
            future = self.actor.execute_command.remote(command, timeout)
            result = ray.get(future)
            return result
        except Exception as e:
            logger.error(f"Error executing command via Ray: {e}")
            return {
                'exit_code': 1,
                'stdout': '',
                'stderr': str(e),
            }
    
    async def _read_file(self, file_path: str) -> dict[str, Any]:
        """Read a file using the Ray actor.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Dict containing file contents or error
        """
        try:
            future = self.actor.read_file.remote(file_path)
            result = ray.get(future)
            return result
        except Exception as e:
            logger.error(f"Error reading file via Ray: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    async def _write_file(self, file_path: str, content: str) -> dict[str, Any]:
        """Write a file using the Ray actor.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Returns:
            Dict containing success status
        """
        try:
            future = self.actor.write_file.remote(file_path, content)
            result = ray.get(future)
            return result
        except Exception as e:
            logger.error(f"Error writing file via Ray: {e}")
            return {
                'success': False,
                'error': str(e),
            }