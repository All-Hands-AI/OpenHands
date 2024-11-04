import subprocess
from functools import wraps
from typing import Any, Callable, TypeVar

from openhands.core.logger import openhands_logger as logger

T = TypeVar('T')

def runtime_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for runtime operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T | None:
            try:
                return func(*args, **kwargs)
            except subprocess.CalledProcessError as e:
                if operation_name == "init_user" and e.returncode == 1:
                    logger.debug(f'User does not exist. Proceeding with user creation.')
                    return None
                logger.error(f'Error during {operation_name}: {e}')
                raise
            except Exception as e:
                logger.error(f'Error during {operation_name}: {e}')
                raise RuntimeError(f'Failed during {operation_name}: {str(e)}')
        return wrapper
    return decorator


def run_command(command: str, check: bool = True) -> tuple[str, int]:
    """Run a shell command and return its output and return code."""
    output = subprocess.run(command, shell=True, capture_output=True)
    return output.stdout.decode(), output.returncode


@runtime_operation("init_user")
def init_user_and_working_directory(
    username: str, user_id: int, initial_pwd: str
) -> int | None:
    """Create working directory and user if not exists.
    It performs the following steps effectively:
    * Creates the Working Directory:
        - Uses mkdir -p to create the directory.
        - Sets ownership to username:root.
        - Adjusts permissions to be readable and writable by group and others.
    * User Verification and Creation:
        - Checks if the user exists using id -u.
        - If the user exists with the correct UID, it skips creation.
        - If the UID differs, it logs a warning and return an updated user_id.
        - If the user doesn't exist, it proceeds to create the user.
    * Sudo Configuration:
        - Appends %sudo ALL=(ALL) NOPASSWD:ALL to /etc/sudoers to grant
            passwordless sudo access to the sudo group.
        - Adds the user to the sudo group with the useradd command, handling
            UID conflicts by incrementing the UID if necessary.

    Args:
        username (str): The username to create.
        user_id (int): The user ID to assign to the user.
        initial_pwd (str): The initial working directory to create.

    Returns:
        int | None: The user ID if it was updated, None otherwise.
    """
    logger.debug(f'Client working directory: {initial_pwd}')
    
    # Create and configure working directory
    commands = [
        f'umask 002; mkdir -p {initial_pwd}',
        f'chown -R {username}:root {initial_pwd}',
        f'chmod g+rw {initial_pwd}'
    ]
    
    for cmd in commands:
        out, code = run_command(cmd)
        if code != 0:
            raise RuntimeError(f'Failed to configure working directory: {out}')
        logger.debug(f'Directory command output: [{out}]')

    # Skip root since it is already created
    if username == 'root':
        return None

    # Check if the username already exists
    result, code = run_command(f'id -u {username}', check=False)
    if code == 0:
        existing_user_id = int(result.strip())
        if existing_user_id == user_id:
            logger.debug(
                f'User `{username}` already has the provided UID {user_id}. Skipping user setup.'
            )
            return None
        logger.warning(
            f'User `{username}` already exists with UID {existing_user_id}. Skipping user setup.'
        )
        return existing_user_id

    # Add sudoer configuration
    sudoer_line = r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
    out, code = run_command(sudoer_line)
    if code != 0:
        raise RuntimeError(f'Failed to add sudoer: {out}')
    logger.debug(f'Added sudoer successfully. Output: [{out}]')

    # Create user
    command = (
        f'useradd -rm -d /home/{username} -s /bin/bash '
        f'-g root -G sudo -u {user_id} {username}'
    )
    out, code = run_command(command)
    if code != 0:
        raise RuntimeError(f'Failed to create user: {out}')
    logger.debug(f'Added user `{username}` successfully with UID {user_id}. Output: [{out}]')
    
    return None

