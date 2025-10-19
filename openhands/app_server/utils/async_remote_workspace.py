import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from openhands.sdk.workspace.models import CommandResult, FileOperationResult

_logger = logging.getLogger(__name__)


@dataclass
class AsyncRemoteWorkspace:
    """Mixin providing remote workspace operations."""

    working_dir: str
    server_url: str
    session_api_key: str | None = None
    client: httpx.AsyncClient = field(default_factory=httpx.AsyncClient)

    def __post_init__(self) -> None:
        # Set up remote host and API key
        self.server_url = self.server_url.rstrip('/')

    def _headers(self):
        headers = {}
        if self.session_api_key:
            headers['X-Session-API-Key'] = self.session_api_key
        return headers

    async def execute_command(
        self,
        command: str,
        cwd: str | Path | None = None,
        timeout: float = 30.0,
    ) -> CommandResult:
        """Execute a bash command on the remote system.

        This method starts a bash command via the remote agent server API,
        then polls for the output until the command completes.

        Args:
            command: The bash command to execute
            cwd: Working directory (optional)
            timeout: Timeout in seconds

        Returns:
            CommandResult: Result with stdout, stderr, exit_code, and other metadata
        """
        _logger.debug(f'Executing remote command: {command}')

        # Step 1: Start the bash command
        payload = {
            'command': command,
            'timeout': int(timeout),
        }
        if cwd is not None:
            payload['cwd'] = str(cwd)

        try:
            # Start the command
            response = await self.client.post(
                f'{self.server_url}/api/bash/execute_bash_command',
                json=payload,
                timeout=timeout + 5.0,  # Add buffer to HTTP timeout
                headers=self._headers(),
            )
            response.raise_for_status()
            bash_command = response.json()
            command_id = bash_command['id']

            _logger.debug(f'Started command with ID: {command_id}')

            # Step 2: Poll for output until command completes
            start_time = time.time()
            stdout_parts = []
            stderr_parts = []
            exit_code = None

            while time.time() - start_time < timeout:
                # Search for all events and filter client-side
                # (workaround for bash service filtering bug)
                search_response = await self.client.get(
                    f'{self.server_url}/api/bash/bash_events/search',
                    params={
                        'sort_order': 'TIMESTAMP',
                        'limit': 100,
                    },
                    timeout=10.0,
                    headers=self._headers(),
                )
                search_response.raise_for_status()
                search_result = search_response.json()

                # Filter for BashOutput events for this command
                for event in search_result.get('items', []):
                    if (
                        event.get('kind') == 'BashOutput'
                        and event.get('command_id') == command_id
                    ):
                        if event.get('stdout'):
                            stdout_parts.append(event['stdout'])
                        if event.get('stderr'):
                            stderr_parts.append(event['stderr'])
                        if event.get('exit_code') is not None:
                            exit_code = event['exit_code']

                # If we have an exit code, the command is complete
                if exit_code is not None:
                    break

                # Wait a bit before polling again
                time.sleep(0.1)

            # If we timed out waiting for completion
            if exit_code is None:
                _logger.warning(f'Command timed out after {timeout} seconds: {command}')
                exit_code = -1
                stderr_parts.append(f'Command timed out after {timeout} seconds')

            # Combine all output parts
            stdout = ''.join(stdout_parts)
            stderr = ''.join(stderr_parts)

            return CommandResult(
                command=command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                timeout_occurred=exit_code == -1 and 'timed out' in stderr,
            )

        except Exception as e:
            _logger.error(f'Remote command execution failed: {e}')
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout='',
                stderr=f'Remote execution error: {str(e)}',
                timeout_occurred=False,
            )

    async def file_upload(
        self,
        source_path: str | Path,
        destination_path: str | Path,
    ) -> FileOperationResult:
        """Upload a file to the remote system.

        Reads the local file and sends it to the remote system via HTTP API.

        Args:
            source_path: Path to the local source file
            destination_path: Path where the file should be uploaded on remote system

        Returns:
            FileOperationResult: Result with success status and metadata
        """
        source = Path(source_path)
        destination = Path(destination_path)

        _logger.debug(f'Remote file upload: {source} -> {destination}')

        try:
            # Read the file content
            with open(source, 'rb') as f:
                file_content = f.read()

            # Prepare the upload
            files = {'file': (source.name, file_content)}
            data = {'destination_path': str(destination)}

            # Make synchronous HTTP call
            response = await self.client.post(
                '/api/files/upload',
                files=files,
                data=data,
                timeout=60.0,
            )
            response.raise_for_status()
            result_data = response.json()

            # Convert the API response to our model
            return FileOperationResult(
                success=result_data.get('success', True),
                source_path=str(source),
                destination_path=str(destination),
                file_size=result_data.get('file_size'),
                error=result_data.get('error'),
            )

        except Exception as e:
            _logger.error(f'Remote file upload failed: {e}')
            return FileOperationResult(
                success=False,
                source_path=str(source),
                destination_path=str(destination),
                error=str(e),
            )

    async def file_download(
        self,
        source_path: str | Path,
        destination_path: str | Path,
    ) -> FileOperationResult:
        """Download a file from the remote system.

        Requests the file from the remote system via HTTP API and saves it locally.

        Args:
            source_path: Path to the source file on remote system
            destination_path: Path where the file should be saved locally

        Returns:
            FileOperationResult: Result with success status and metadata
        """
        source = Path(source_path)
        destination = Path(destination_path)

        _logger.debug(f'Remote file download: {source} -> {destination}')

        try:
            # Request the file from remote system
            params = {'file_path': str(source)}

            # Make synchronous HTTP call
            response = await self.client.get(
                '/api/files/download',
                params=params,
                timeout=60.0,
            )
            response.raise_for_status()

            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Write the file content
            with open(destination, 'wb') as f:
                f.write(response.content)

            return FileOperationResult(
                success=True,
                source_path=str(source),
                destination_path=str(destination),
                file_size=len(response.content),
            )

        except Exception as e:
            _logger.error(f'Remote file download failed: {e}')
            return FileOperationResult(
                success=False,
                source_path=str(source),
                destination_path=str(destination),
                error=str(e),
            )
