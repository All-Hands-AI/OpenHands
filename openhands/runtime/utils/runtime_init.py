import os
import subprocess

from openhands.core.logger import openhands_logger as logger


def init_user_and_working_directory(
    username: str, user_id: int, initial_cwd: str
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
        initial_cwd (str): The initial working directory to create.

    Returns:
        int | None: The user ID if it was updated, None otherwise.
    """
    # if username is CURRENT_USER, then we don't need to do anything
    # This is specific to the local runtime
    if username == os.getenv('USER') and username not in ['root', 'openhands']:
        return None

    # First create the working directory, independent of the user
    logger.debug(f'Client working directory: {initial_cwd}')
    command = f'umask 002; mkdir -p {initial_cwd}'
    output = subprocess.run(command, shell=True, capture_output=True)
    out_str = output.stdout.decode()

    command = f'chown -R {username}:root {initial_cwd}'
    output = subprocess.run(command, shell=True, capture_output=True)
    out_str += output.stdout.decode()

    command = f'chmod g+rw {initial_cwd}'
    output = subprocess.run(command, shell=True, capture_output=True)
    out_str += output.stdout.decode()
    logger.debug(f'Created working directory. Output: [{out_str}]')

    # Skip root since it is already created
    if username == 'root':
        return None

    # Check if the username already exists
    existing_user_id = -1
    try:
        result = subprocess.run(
            f'id -u {username}', shell=True, check=True, capture_output=True
        )
        existing_user_id = int(result.stdout.decode().strip())

        # The user ID already exists, skip setup
        if existing_user_id == user_id:
            logger.debug(
                f'User `{username}` already has the provided UID {user_id}. Skipping user setup.'
            )
        else:
            logger.warning(
                f'User `{username}` already exists with UID {existing_user_id}. Skipping user setup.'
            )
            return existing_user_id
        return None
    except subprocess.CalledProcessError as e:
        # Returncode 1 indicates, that the user does not exist yet
        if e.returncode == 1:
            logger.debug(
                f'User `{username}` does not exist. Proceeding with user creation.'
            )
        else:
            logger.error(f'Error checking user `{username}`, skipping setup:\n{e}\n')
            raise

    # Add sudoer
    sudoer_line = r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
    output = subprocess.run(sudoer_line, shell=True, capture_output=True)
    if output.returncode != 0:
        raise RuntimeError(f'Failed to add sudoer: {output.stderr.decode()}')
    logger.debug(f'Added sudoer successfully. Output: [{output.stdout.decode()}]')

    command = (
        f'useradd -rm -d /home/{username} -s /bin/bash '
        f'-g root -G sudo -u {user_id} {username}'
    )
    output = subprocess.run(command, shell=True, capture_output=True)
    if output.returncode == 0:
        logger.debug(
            f'Added user `{username}` successfully with UID {user_id}. Output: [{output.stdout.decode()}]'
        )
    else:
        raise RuntimeError(
            f'Failed to create user `{username}` with UID {user_id}. Output: [{output.stderr.decode()}]'
        )
    return None
