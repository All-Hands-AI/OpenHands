import importlib.resources
import json
import os
import pathlib
import subprocess
import tempfile
import urllib.request
from urllib.error import URLError

from openhands.core.logger import openhands_logger as logger


def download_latest_vsix_from_github() -> str | None:
    """Download latest .vsix from GitHub releases.

    Returns:
        Path to downloaded .vsix file, or None if failed
    """
    api_url = 'https://api.github.com/repos/All-Hands-AI/OpenHands/releases'
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            if response.status != 200:
                logger.debug(
                    f'GitHub API request failed with status: {response.status}'
                )
                return None
            releases = json.loads(response.read().decode())
            # The GitHub API returns releases in reverse chronological order (newest first).
            # We iterate through them and use the first one that matches our extension prefix.
            for release in releases:
                if release.get('tag_name', '').startswith('ext-v'):
                    for asset in release.get('assets', []):
                        if asset.get('name', '').endswith('.vsix'):
                            download_url = asset.get('browser_download_url')
                            if not download_url:
                                continue
                            with urllib.request.urlopen(
                                download_url, timeout=30
                            ) as download_response:
                                if download_response.status != 200:
                                    logger.debug(
                                        f'Failed to download .vsix with status: {download_response.status}'
                                    )
                                    continue
                                with tempfile.NamedTemporaryFile(
                                    delete=False, suffix='.vsix'
                                ) as tmp_file:
                                    tmp_file.write(download_response.read())
                                    return tmp_file.name
                    # Found the latest extension release but no .vsix asset
                    return None
    except (URLError, TimeoutError, json.JSONDecodeError) as e:
        logger.debug(f'Failed to download from GitHub releases: {e}')
        return None
    return None


def attempt_vscode_extension_install():
    """
    Checks if running in a supported editor and attempts to install the OpenHands companion extension.
    This is a best-effort, one-time attempt.
    """
    # 1. Check if we are in a supported editor environment
    is_vscode_like = os.environ.get('TERM_PROGRAM') == 'vscode'
    is_windsurf = (
        os.environ.get('__CFBundleIdentifier') == 'com.exafunction.windsurf'
        or 'windsurf' in os.environ.get('PATH', '').lower()
        or any(
            'windsurf' in val.lower()
            for val in os.environ.values()
            if isinstance(val, str)
        )
    )
    if not (is_vscode_like or is_windsurf):
        return

    # 2. Determine editor-specific commands and flags
    if is_windsurf:
        editor_command, editor_name, flag_suffix = 'surf', 'Windsurf', 'windsurf'
    else:
        editor_command, editor_name, flag_suffix = 'code', 'VS Code', 'vscode'

    # 3. Check if we've already attempted installation. If so, do nothing.
    flag_dir = pathlib.Path.home() / '.openhands'
    flag_file = flag_dir / f'.{flag_suffix}_extension_install_attempted'
    try:
        flag_dir.mkdir(parents=True, exist_ok=True)
        if flag_file.exists():
            return  # Already attempted, exit.
    except OSError as e:
        logger.debug(
            f'Could not create or check {editor_name} extension flag directory: {e}'
        )
        return  # Don't proceed if we can't manage the flag.

    # If we've reached here, it's our first attempt.
    # From now on, we create the flag file at the end, regardless of success.
    try:
        print(
            f'INFO: First-time setup: attempting to install the OpenHands {editor_name} extension...'
        )

        # Attempt 1: Download from GitHub Releases (the new primary method)
        vsix_path_from_github = download_latest_vsix_from_github()
        if vsix_path_from_github:
            try:
                process = subprocess.run(
                    [
                        editor_command,
                        '--install-extension',
                        vsix_path_from_github,
                        '--force',
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if process.returncode == 0:
                    print(
                        f'INFO: OpenHands {editor_name} extension installed successfully from GitHub.'
                    )
                    return  # Success! We are done.
                else:
                    logger.debug(
                        f'Failed to install .vsix from GitHub: {process.stderr.strip()}'
                    )
            finally:
                # Clean up the downloaded file
                if os.path.exists(vsix_path_from_github):
                    try:
                        os.remove(vsix_path_from_github)
                    except OSError as e:
                        logger.debug(
                            f'Failed to delete temporary file {vsix_path_from_github}: {e}'
                        )

        # If GitHub download failed, fall back to the original methods.
        extension_id = 'openhands.openhands-vscode'

        # Attempt 2: Install from bundled .vsix
        try:
            vsix_filename = 'openhands-vscode-0.0.1.vsix'
            with importlib.resources.as_file(
                importlib.resources.files('openhands').joinpath(
                    'integrations', 'vscode', vsix_filename
                )
            ) as vsix_path:
                if vsix_path.exists():
                    process = subprocess.run(
                        [
                            editor_command,
                            '--install-extension',
                            str(vsix_path),
                            '--force',
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if process.returncode == 0:
                        print(
                            f'INFO: Bundled {editor_name} extension installed successfully.'
                        )
                        return  # Success!
                    else:
                        logger.debug(
                            f'Bundled .vsix installation failed: {process.stderr.strip()}'
                        )
        except Exception as e:
            logger.debug(
                f'Could not locate bundled .vsix: {e}. Falling back to Marketplace.'
            )

        # Attempt 3: Install from Marketplace
        try:
            process = subprocess.run(
                [editor_command, '--install-extension', extension_id, '--force'],
                capture_output=True,
                text=True,
                check=False,
            )
            if process.returncode == 0:
                print(
                    f'INFO: {editor_name} extension installed successfully from the Marketplace.'
                )
                return  # Success!
            else:
                logger.debug(
                    f'Marketplace installation failed: {process.stderr.strip()}'
                )
        except FileNotFoundError:
            print(
                f"INFO: To complete {editor_name} integration, please ensure the '{editor_command}' command-line tool is in your PATH."
            )
        except Exception as e:
            logger.debug(
                f'An unexpected error occurred trying to install from the Marketplace: {e}'
            )

        # If all attempts failed, inform the user.
        print(
            f"INFO: Automatic installation failed. Please install '{extension_id}' manually from the {editor_name} Marketplace."
        )

    finally:
        # 4. Create the flag file AFTER all attempts are made, ensuring we only try this whole process once.
        try:
            flag_file.touch()
        except OSError as e:
            logger.debug(
                f'Could not create {editor_name} extension attempt flag file: {e}'
            )
