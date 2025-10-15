"""Process-based sandbox service implementation.

This service creates sandboxes by spawning separate agent server processes,
each running as a specific user within a dedicated directory.
"""

import asyncio
import logging
import os
import pwd
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator

import base62
import httpx
import psutil
from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

from openhands.agent_server.utils import utc_now
from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.sandbox_models import (
    AGENT_SERVER,
    VSCODE,
    ExposedUrl,
    SandboxInfo,
    SandboxPage,
    SandboxStatus,
)
from openhands.app_server.sandbox.sandbox_service import (
    SandboxService,
    SandboxServiceInjector,
)
from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecService
from openhands.app_server.services.injector import InjectorState

_logger = logging.getLogger(__name__)


class ProcessInfo(BaseModel):
    """Information about a running process."""

    pid: int
    port: int
    user: str
    working_dir: str
    session_api_key: str
    created_at: datetime
    sandbox_spec_id: str

    model_config = ConfigDict(frozen=True)


@dataclass
class ProcessSandboxService(SandboxService):
    """Sandbox service that spawns separate agent server processes.

    Each sandbox is implemented as a separate Python process running the
    action execution server, with each process:
    - Running as a specific user
    - Operating in a dedicated directory
    - Listening on a unique port
    - Having its own session API key
    """

    sandbox_spec_service: SandboxSpecService
    base_working_dir: str
    base_port: int
    python_executable: str
    action_server_module: str
    default_user: str
    health_check_path: str
    httpx_client: httpx.AsyncClient

    # Runtime state
    processes: dict[str, ProcessInfo] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the service after dataclass creation."""
        # Ensure base working directory exists
        os.makedirs(self.base_working_dir, exist_ok=True)

    def _find_unused_port(self) -> int:
        """Find an unused port starting from base_port."""
        port = self.base_port
        while port < self.base_port + 10000:  # Try up to 10000 ports
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                port += 1
        raise SandboxError('No available ports found')

    def _get_user_info(self, username: str) -> tuple[int, int]:
        """Get user ID and group ID for a username."""
        try:
            user_info = pwd.getpwnam(username)
            return user_info.pw_uid, user_info.pw_gid
        except KeyError:
            # If user doesn't exist, use current user
            _logger.warning(f'User {username} not found, using current user')
            return os.getuid(), os.getgid()

    def _create_sandbox_directory(self, sandbox_id: str, user: str) -> str:
        """Create a dedicated directory for the sandbox."""
        sandbox_dir = os.path.join(self.base_working_dir, sandbox_id)
        os.makedirs(sandbox_dir, exist_ok=True)

        # Set ownership to the specified user
        try:
            uid, gid = self._get_user_info(user)
            os.chown(sandbox_dir, uid, gid)
            # Set permissions to allow user full access
            os.chmod(sandbox_dir, 0o755)
        except (OSError, PermissionError) as e:
            _logger.warning(f'Could not set ownership of {sandbox_dir}: {e}')

        return sandbox_dir

    async def _start_agent_process(
        self,
        sandbox_id: str,
        port: int,
        working_dir: str,
        user: str,
        session_api_key: str,
        sandbox_spec: Any,
    ) -> subprocess.Popen:
        """Start the agent server process."""

        # Prepare environment variables
        env = os.environ.copy()
        env.update(sandbox_spec.initial_env)
        env['SESSION_API_KEY'] = session_api_key

        # Prepare command arguments
        cmd = [
            self.python_executable,
            '-m',
            self.action_server_module,
            str(port),
            '--working-dir',
            working_dir,
            '--username',
            user,
        ]

        # Add user ID if we can determine it
        try:
            uid, _ = self._get_user_info(user)
            cmd.extend(['--user-id', str(uid)])
        except Exception:
            pass

        # Add plugins if specified in sandbox spec
        if hasattr(sandbox_spec, 'plugins') and sandbox_spec.plugins:
            cmd.extend(['--plugins'] + sandbox_spec.plugins)

        _logger.info(
            f'Starting agent process for sandbox {sandbox_id}: {" ".join(cmd)}'
        )

        try:
            # Start the process
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=self._preexec_fn(user) if user != 'root' else None,
            )

            # Wait a moment for the process to start
            await asyncio.sleep(1)

            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise SandboxError(f'Agent process failed to start: {stderr.decode()}')

            return process

        except Exception as e:
            raise SandboxError(f'Failed to start agent process: {e}')

    def _preexec_fn(self, username: str):
        """Create a preexec function to switch user before process execution."""

        def preexec():
            try:
                uid, gid = self._get_user_info(username)
                os.setgid(gid)
                os.setuid(uid)
            except Exception as e:
                _logger.error(f'Failed to switch to user {username}: {e}')

        return preexec

    async def _wait_for_server_ready(self, port: int, timeout: int = 30) -> bool:
        """Wait for the agent server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await self.httpx_client.get(
                    f'http://localhost:{port}/alive', timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        return True
            except Exception:
                pass
            await asyncio.sleep(1)
        return False

    def _get_process_status(self, process_info: ProcessInfo) -> SandboxStatus:
        """Get the status of a process."""
        try:
            process = psutil.Process(process_info.pid)
            if process.is_running():
                status = process.status()
                if status == psutil.STATUS_RUNNING:
                    return SandboxStatus.RUNNING
                elif status == psutil.STATUS_STOPPED:
                    return SandboxStatus.PAUSED
                else:
                    return SandboxStatus.STARTING
            else:
                return SandboxStatus.MISSING
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return SandboxStatus.MISSING

    async def _process_to_sandbox_info(
        self, sandbox_id: str, process_info: ProcessInfo
    ) -> SandboxInfo:
        """Convert process info to sandbox info."""
        status = self._get_process_status(process_info)

        exposed_urls = None
        session_api_key = None

        if status == SandboxStatus.RUNNING:
            # Check if server is actually responding
            try:
                response = await self.httpx_client.get(
                    f'http://localhost:{process_info.port}{self.health_check_path}',
                    timeout=5.0,
                )
                if response.status_code == 200:
                    exposed_urls = [
                        ExposedUrl(
                            name=AGENT_SERVER,
                            url=f'http://localhost:{process_info.port}',
                        ),
                        ExposedUrl(
                            name=VSCODE,
                            url=f'http://localhost:{process_info.port + 1}',  # VSCode typically on port+1
                        ),
                    ]
                    session_api_key = process_info.session_api_key
                else:
                    status = SandboxStatus.ERROR
            except Exception:
                status = SandboxStatus.ERROR

        return SandboxInfo(
            id=sandbox_id,
            created_by_user_id=process_info.user,
            sandbox_spec_id=process_info.sandbox_spec_id,
            status=status,
            session_api_key=session_api_key,
            exposed_urls=exposed_urls,
            created_at=process_info.created_at,
        )

    async def search_sandboxes(
        self,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxPage:
        """Search for sandboxes."""
        # Get all process infos
        all_processes = list(self.processes.items())

        # Sort by creation time (newest first)
        all_processes.sort(key=lambda x: x[1].created_at, reverse=True)

        # Apply pagination
        start_idx = 0
        if page_id:
            try:
                start_idx = int(page_id)
            except ValueError:
                start_idx = 0

        end_idx = start_idx + limit
        paginated_processes = all_processes[start_idx:end_idx]

        # Convert to sandbox infos
        items = []
        for sandbox_id, process_info in paginated_processes:
            sandbox_info = await self._process_to_sandbox_info(sandbox_id, process_info)
            items.append(sandbox_info)

        # Determine next page ID
        next_page_id = None
        if end_idx < len(all_processes):
            next_page_id = str(end_idx)

        return SandboxPage(items=items, next_page_id=next_page_id)

    async def get_sandbox(self, sandbox_id: str) -> SandboxInfo | None:
        """Get a single sandbox."""
        process_info = self.processes.get(sandbox_id)
        if process_info is None:
            return None

        return await self._process_to_sandbox_info(sandbox_id, process_info)

    async def start_sandbox(self, sandbox_spec_id: str | None = None) -> SandboxInfo:
        """Start a new sandbox."""
        # Get sandbox spec
        if sandbox_spec_id is None:
            sandbox_spec = await self.sandbox_spec_service.get_default_sandbox_spec()
        else:
            sandbox_spec_maybe = await self.sandbox_spec_service.get_sandbox_spec(
                sandbox_spec_id
            )
            if sandbox_spec_maybe is None:
                raise ValueError('Sandbox Spec not found')
            sandbox_spec = sandbox_spec_maybe

        # Generate unique sandbox ID and session API key
        sandbox_id = base62.encodebytes(os.urandom(16))
        session_api_key = base62.encodebytes(os.urandom(32))

        # Find available port
        port = self._find_unused_port()

        # Create sandbox directory
        working_dir = self._create_sandbox_directory(sandbox_id, self.default_user)

        # Start the agent process
        process = await self._start_agent_process(
            sandbox_id=sandbox_id,
            port=port,
            working_dir=working_dir,
            user=self.default_user,
            session_api_key=session_api_key,
            sandbox_spec=sandbox_spec,
        )

        # Store process info
        process_info = ProcessInfo(
            pid=process.pid,
            port=port,
            user=self.default_user,
            working_dir=working_dir,
            session_api_key=session_api_key,
            created_at=utc_now(),
            sandbox_spec_id=sandbox_spec.id,
        )
        self.processes[sandbox_id] = process_info

        # Wait for server to be ready
        if not await self._wait_for_server_ready(port):
            # Clean up if server didn't start properly
            await self.delete_sandbox(sandbox_id)
            raise SandboxError('Agent server failed to start properly')

        return await self._process_to_sandbox_info(sandbox_id, process_info)

    async def resume_sandbox(self, sandbox_id: str) -> bool:
        """Resume a paused sandbox."""
        process_info = self.processes.get(sandbox_id)
        if process_info is None:
            return False

        try:
            process = psutil.Process(process_info.pid)
            if process.status() == psutil.STATUS_STOPPED:
                process.resume()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    async def pause_sandbox(self, sandbox_id: str) -> bool:
        """Pause a running sandbox."""
        process_info = self.processes.get(sandbox_id)
        if process_info is None:
            return False

        try:
            process = psutil.Process(process_info.pid)
            if process.is_running():
                process.suspend()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox."""
        process_info = self.processes.get(sandbox_id)
        if process_info is None:
            return False

        try:
            # Terminate the process
            process = psutil.Process(process_info.pid)
            if process.is_running():
                # Try graceful termination first
                process.terminate()
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Force kill if graceful termination fails
                    process.kill()
                    process.wait(timeout=5)

            # Clean up the working directory
            import shutil

            if os.path.exists(process_info.working_dir):
                shutil.rmtree(process_info.working_dir, ignore_errors=True)

            # Remove from our tracking
            del self.processes[sandbox_id]

            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            _logger.warning(f'Error deleting sandbox {sandbox_id}: {e}')
            # Still remove from tracking even if cleanup failed
            if sandbox_id in self.processes:
                del self.processes[sandbox_id]
            return True


class ProcessSandboxServiceInjector(SandboxServiceInjector):
    """Dependency injector for process sandbox services."""

    base_working_dir: str = Field(
        default='/tmp/openhands-sandboxes',
        description='Base directory for sandbox working directories',
    )
    base_port: int = Field(
        default=8000, description='Base port number for agent servers'
    )
    python_executable: str = Field(
        default=sys.executable,
        description='Python executable to use for agent processes',
    )
    action_server_module: str = Field(
        default='openhands.runtime.action_execution_server',
        description='Python module for the action execution server',
    )
    default_user: str = Field(
        default='openhands', description='Default user to run sandbox processes as'
    )
    health_check_path: str = Field(
        default='/alive', description='Health check endpoint path'
    )

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[SandboxService, None]:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import (
            get_httpx_client,
            get_sandbox_spec_service,
        )

        async with (
            get_httpx_client(state) as httpx_client,
            get_sandbox_spec_service(state) as sandbox_spec_service,
        ):
            yield ProcessSandboxService(
                sandbox_spec_service=sandbox_spec_service,
                base_working_dir=self.base_working_dir,
                base_port=self.base_port,
                python_executable=self.python_executable,
                action_server_module=self.action_server_module,
                default_user=self.default_user,
                health_check_path=self.health_check_path,
                httpx_client=httpx_client,
            )
