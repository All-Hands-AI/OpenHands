import asyncio
import os
import pwd
import sys
from typing import Any, Optional

from openhands.runtime.base import CommandResult


class AsyncBashSession:
    @staticmethod
    async def execute(
        command: str, work_dir: str, username: Optional[str] = None
    ) -> CommandResult:
        """Execute a command in the bash session asynchronously."""
        work_dir = os.path.abspath(work_dir)

        if not os.path.exists(work_dir):
            raise ValueError(f'Work directory {work_dir} does not exist.')

        command = command.strip()
        if not command:
            return CommandResult(content='', exit_code=0)

        # Create subprocess arguments
        subprocess_kwargs: dict[str, Any] = {
            'stdout': asyncio.subprocess.PIPE,
            'stderr': asyncio.subprocess.PIPE,
            'cwd': work_dir,
        }

        # Only apply user-specific settings on non-Windows platforms
        if username and sys.platform != 'win32':
            try:
                user_info = pwd.getpwnam(username)
                # Start with current environment to preserve important variables
                env = os.environ.copy()
                # Update with user-specific variables
                env.update(
                    {
                        'HOME': user_info.pw_dir,
                        'USER': username,
                        'LOGNAME': username,
                    }
                )
                subprocess_kwargs['env'] = env
                subprocess_kwargs['user'] = username
            except KeyError:
                raise ValueError(f'User {username} does not exist.')

        # Prepare to run the command
        try:
            process = await asyncio.subprocess.create_subprocess_shell(
                command, **subprocess_kwargs
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=30
                )
                output = stdout.decode('utf-8')

                if stderr:
                    stderr_text = stderr.decode('utf-8')
                    # Append stderr to output instead of replacing it
                    if stderr_text.strip():
                        output += f'\n{stderr_text}'
                        print(f'!##! Error running command: {stderr_text}')

                return CommandResult(content=output, exit_code=process.returncode or 0)

            except asyncio.TimeoutError:
                process.terminate()

                # Allow a brief moment for cleanup
                try:
                    await asyncio.wait_for(process.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    process.kill()  # Force kill if it doesn't terminate cleanly

                return CommandResult(content='Command timed out.', exit_code=-1)

        except Exception as e:
            return CommandResult(
                content=f'Error running command: {str(e)}', exit_code=-1
            )
