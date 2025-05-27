import asyncio
import os

from openhands.runtime.base import CommandResult


class AsyncBashSession:
    @staticmethod
    async def execute(
        command: str, work_dir: str, username: str | None = None
    ) -> CommandResult:
        """Execute a command in the bash session asynchronously."""
        work_dir = os.path.abspath(work_dir)

        if not os.path.exists(work_dir):
            raise ValueError(f'Work directory {work_dir} does not exist.')

        command = command.strip()
        if not command:
            return CommandResult(content='', exit_code=0)

        # Handle username similar to BashSession
        if username in ['root', 'openhands']:
            # Use sudo with bash -c to properly handle command substitution and special characters
            # Replace single quotes with escaped double quotes to avoid issues with nested commands
            escaped_command = command.replace("'", '\\"')
            command = f'sudo -u {username} bash -c "{escaped_command}"'

        try:
            process = await asyncio.subprocess.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=30
                )
                output = stdout.decode('utf-8')

                if stderr:
                    output = stderr.decode('utf-8')
                    print(f'!##! Error running command: {stderr.decode("utf-8")}')

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
