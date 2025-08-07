import os
import subprocess
import sys

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
    # If running on Windows, just create the directory and return
    if sys.platform == 'win32':
        logger.debug('Running on Windows, skipping Unix-specific user setup')
        logger.debug(f'Client working directory: {initial_cwd}')

        # Create the working directory if it doesn't exist
        os.makedirs(initial_cwd, exist_ok=True)
        logger.debug(f'Created working directory: {initial_cwd}')

        return None

    # if username is CURRENT_USER, then we don't need to do anything
    # This is specific to the local runtime
    if username == os.getenv('USER') and username not in ['root', 'openhands']:
        return None

    # Skip root since it is already created
    if username != 'root':
        # Check if the username already exists
        logger.info(f'Attempting to create user `{username}` with UID {user_id}.')
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
                logger.info(
                    f'User `{username}` does not exist. Proceeding with user creation.'
                )
            else:
                logger.error(
                    f'Error checking user `{username}`, skipping setup:\n{e}\n'
                )
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

    # First create the working directory, independent of the user
    logger.debug(f'Client working directory: {initial_cwd}')
    command = f'umask 002; mkdir -p {initial_cwd}'
    output = subprocess.run(command, shell=True, capture_output=True)
    out_str = output.stdout.decode()
    logger.debug(f'mkdir command result: returncode={output.returncode}, stdout=[{out_str}], stderr=[{output.stderr.decode()}]')

    # Check current ownership before changing it
    check_cmd = f'ls -la {initial_cwd}'
    check_output = subprocess.run(check_cmd, shell=True, capture_output=True)
    logger.debug(f'Current ownership: {check_output.stdout.decode()}')

    # Check if we're running as root
    whoami_output = subprocess.run('whoami', shell=True, capture_output=True)
    current_user = whoami_output.stdout.decode().strip()
    logger.debug(f'Current user: {current_user}')
    
    # Use sudo only if not running as root
    sudo_prefix = '' if current_user == 'root' else 'sudo '
    
    command = f'{sudo_prefix}chown -R {username}:{username} {initial_cwd}'
    logger.debug(f'Executing chown command: {command}')
    output = subprocess.run(command, shell=True, capture_output=True)
    out_str += output.stdout.decode()
    logger.debug(f'chown command result: returncode={output.returncode}, stdout=[{output.stdout.decode()}], stderr=[{output.stderr.decode()}]')
    if output.returncode != 0 or output.stderr:
        err_str = output.stderr.decode()
        logger.error(f'chown command failed: returncode={output.returncode}, stderr: {err_str}')
        out_str += f' [stderr: {err_str}]'

    command = f'{sudo_prefix}chmod g+rw {initial_cwd}'
    logger.debug(f'Executing chmod command: {command}')
    output = subprocess.run(command, shell=True, capture_output=True)
    out_str += output.stdout.decode()
    logger.debug(f'chmod command result: returncode={output.returncode}, stdout=[{output.stdout.decode()}], stderr=[{output.stderr.decode()}]')
    if output.returncode != 0 or output.stderr:
        err_str = output.stderr.decode()
        logger.error(f'chmod command failed: returncode={output.returncode}, stderr: {err_str}')
        out_str += f' [stderr: {err_str}]'

    # Verify final ownership
    check_cmd = f'ls -la {initial_cwd}'
    check_output = subprocess.run(check_cmd, shell=True, capture_output=True)
    final_ownership = check_output.stdout.decode()
    logger.debug(f'Final ownership: {final_ownership}')
    
    # If chown failed and directory is still owned by root, try alternative approaches
    if 'root root' in final_ownership and username != 'root':
        logger.warning(f'Directory {initial_cwd} is still owned by root, trying alternative approaches')
        
        # Try to make it writable for the user's group
        alt_command = f'{sudo_prefix}chmod -R g+rwx {initial_cwd}'
        logger.debug(f'Executing alternative chmod command: {alt_command}')
        alt_output = subprocess.run(alt_command, shell=True, capture_output=True)
        logger.debug(f'Alternative chmod result: returncode={alt_output.returncode}, stderr=[{alt_output.stderr.decode()}]')
        
        # Try to add the user to the root group (as a last resort)
        if alt_output.returncode != 0:
            group_command = f'{sudo_prefix}usermod -aG root {username}'
            logger.debug(f'Executing usermod command: {group_command}')
            group_output = subprocess.run(group_command, shell=True, capture_output=True)
            logger.debug(f'Usermod result: returncode={group_output.returncode}, stderr=[{group_output.stderr.decode()}]')
    
    logger.debug(f'Created working directory. Output: [{out_str}]')

    return None
