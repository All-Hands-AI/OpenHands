import os
import shutil
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

    # Defensive guard: never attempt to create a non-root user with UID 0
    try:
        user_id = int(user_id)
    except Exception:
        user_id = 1000
    if username != 'root' and user_id == 0:
        logger.warning(
            'Received UID 0 for non-root user; overriding to 1000 to avoid conflict with root'
        )
        user_id = 1000

    # if username is CURRENT_USER, then we don't need to do anything
    # This is specific to the local runtime
    if username == os.getenv('USER') and username not in ['root', 'openhands']:
        return None

    # First create the working directory
    logger.debug(f'Client working directory: {initial_cwd}')
    output = subprocess.run(
        f'umask 002; mkdir -p {initial_cwd}', shell=True, capture_output=True
    )
    out_str = output.stdout.decode()
    logger.debug(f'Ensured working directory exists. Output: [{out_str}]')

    # If running as root user, no need to create another user
    if username == 'root':
        # Make sure directory is group-writable
        subprocess.run(f'chmod g+rw {initial_cwd}', shell=True, capture_output=True)
        return None

    # Ensure the user exists before attempting chown
    existing_user_id = -1
    try:
        result = subprocess.run(
            f'id -u {username}', shell=True, check=True, capture_output=True
        )
        existing_user_id = int(result.stdout.decode().strip())
        if existing_user_id != user_id:
            logger.warning(
                f'User `{username}` already exists with UID {existing_user_id}. Skipping user setup.'
            )
            user_id = existing_user_id
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            logger.debug(
                f'User `{username}` does not exist. Proceeding with user creation.'
            )
            # Add sudoer (passwordless)
            sudoer_line = r"echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"
            output = subprocess.run(sudoer_line, shell=True, capture_output=True)
            if output.returncode != 0:
                raise RuntimeError(f'Failed to add sudoer: {output.stderr.decode()}')
            # Create the user with the provided UID
            cmd_useradd = (
                f'useradd -rm -d /home/{username} -s /bin/bash '
                f'-g root -G sudo -u {user_id} {username}'
            )
            output = subprocess.run(cmd_useradd, shell=True, capture_output=True)
            if output.returncode == 0:
                logger.debug(
                    f'Added user `{username}` successfully with UID {user_id}. Output: [{output.stdout.decode()}]'
                )
            else:
                raise RuntimeError(
                    f'Failed to create user `{username}` with UID {user_id}. Output: [{output.stderr.decode()}]'
                )
        else:
            logger.error(f'Error checking user `{username}`, skipping setup:\n{e}\n')
            raise

    # Now that the user exists, set ownership and permissions on the workspace
    subprocess.run(
        f'chown -R {username}:root {initial_cwd}', shell=True, capture_output=True
    )
    subprocess.run(f'chmod g+rw {initial_cwd}', shell=True, capture_output=True)

    # Configure git for the target user: safe.directory and global hooks/template
    try:
        # Ensure hooks directory exists and has our prepare-commit-msg
        hooks_root = '/openhands/git-hooks'
        hooks_dir = os.path.join(hooks_root, 'hooks')
        os.makedirs(hooks_dir, exist_ok=True)
        hook_src = (
            '/openhands/code/openhands/runtime/utils/git_hooks/prepare-commit-msg'
        )
        hook_dest = os.path.join(hooks_dir, 'prepare-commit-msg')
        if os.path.exists(hook_src):
            shutil.copyfile(hook_src, hook_dest)
            os.chmod(hook_dest, 0o755)
        else:
            # Fallback: write a minimal prepare-commit-msg hook that adds co-authorship
            with open(hook_dest, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write('FILE="$1"\n')
                f.write(
                    'if ! grep -qi "co-authored-by.*openhands.*<openhands@all-hands.dev>" "$FILE" 2>/dev/null; then\n'
                )
                f.write('  echo "" >> "$FILE"\n')
                f.write('  echo "" >> "$FILE"\n')
                f.write(
                    '  echo "Co-authored-by: openhands <openhands@all-hands.dev>" >> "$FILE"\n'
                )
                f.write('fi\n')
            os.chmod(hook_dest, 0o755)

        env = dict(os.environ)
        env['HOME'] = f'/home/{username}'
        # Avoid dubious ownership errors
        subprocess.run(
            ['git', 'config', '--global', '--add', 'safe.directory', initial_cwd],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        # Ensure co-authorship hook is enabled for all repos/actions
        subprocess.run(
            ['git', 'config', '--global', 'core.hooksPath', hooks_dir],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        subprocess.run(
            ['git', 'config', '--global', 'init.templateDir', hooks_root],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    except Exception:
        pass

    return None
