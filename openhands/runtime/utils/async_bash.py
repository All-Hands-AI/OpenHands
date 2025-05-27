import asyncio
import os
import pwd

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

        # Prepare to run the command
        try:
            # If a specific username is provided, use preexec_fn to set the user
            preexec_fn = None
            if username in ['root', 'openhands']:
                # We'll use the subprocess directly with the correct user
                # This avoids any command escaping issues
                def set_user():
                    # Get user info
                    user_info = pwd.getpwnam(username)
                    # Set the user and group IDs
                    os.setgid(user_info.pw_gid)
                    os.setuid(user_info.pw_uid)

                preexec_fn = set_user

            # Create the subprocess with the appropriate user if specified
            process = await asyncio.subprocess.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                preexec_fn=preexec_fn,
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
