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
                logger.warning(
                    f'GitHub API request failed with status: {response.status}'
                )
                return None
            releases = json.loads(response.read().decode())
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
                                    logger.warning(
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
        logger.warning(f'Failed to download from GitHub releases: {e}')
        return None
    return None


def attempt_vscode_extension_install():
    """
    Checks if running in VS Code/Windsurf and attempts to install the OpenHands companion extension.
    This is a best-effort, one-time attempt.
    """
    # Attempt 0: Download from GitHub Releases
    vsix_path_from_github = download_latest_vsix_from_github()
    if vsix_path_from_github:
        try:
            editor_command = 'code'
            is_windsurf = 'windsurf' in os.environ.get('TERM_PROGRAM', '')
            if is_windsurf:
                editor_command = 'surf'

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
                    'INFO: OpenHands VS Code extension installed successfully from GitHub.'
                )
                # Mark as attempted and return
                flag_dir = pathlib.Path.home() / '.openhands'
                flag_file = flag_dir / '.vscode_extension_install_attempted'
                try:
                    flag_dir.mkdir(parents=True, exist_ok=True)
                    flag_file.touch()
                except OSError:
                    pass  # If we can't write the flag, we'll just try again next time.
                return
            else:
                logger.warning(f'Failed to install .vsix from GitHub: {process.stderr}')
        finally:
            os.remove(vsix_path_from_github)

    # Detect if we're in VSCode or Windsurf
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
        return  # Not in a supported editor

    # Determine the command and editor
    if is_windsurf:
        editor_command = 'surf'
        editor_name = 'Windsurf'
        flag_suffix = 'windsurf'
    else:
        editor_command = 'code'
        editor_name = 'VS Code'
        flag_suffix = 'vscode'

    flag_dir = pathlib.Path.home() / '.openhands'
    flag_file = flag_dir / f'.{flag_suffix}_extension_install_attempted'

    try:
        flag_dir.mkdir(parents=True, exist_ok=True)
        if flag_file.exists():
            return  # Already attempted
    except OSError as e:
        logger.warning(
            f'Could not create or check {editor_name} extension flag directory: {e}'
        )
        return  # Don't proceed if we can't manage the flag

    print(f'INFO: Setting up OpenHands {editor_name} integration...')
    extension_id = 'openhands.openhands-vscode'
    vsix_filename = 'openhands-vscode-0.0.1.vsix'
    install_command_executed = False
    installation_successful_message_shown = False

    # Attempt 1: Install from bundled .vsix
    try:
        with importlib.resources.as_file(
            importlib.resources.files('openhands').joinpath(
                'integrations', 'vscode', vsix_filename
            )
        ) as vsix_path:
            if vsix_path.exists():
                # print(f"DEBUG: Found bundled .vsix at '{vsix_path}'. Attempting install...") # Optional debug
                process = subprocess.run(
                    [editor_command, '--install-extension', str(vsix_path), '--force'],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                install_command_executed = True
                if process.returncode == 0:
                    print(
                        f'INFO: {editor_name} extension installation command sent successfully.'
                        f' Please reload {editor_name} if prompted to activate the extension.'
                    )
                    installation_successful_message_shown = True
                else:
                    logger.warning(
                        f'Bundled .vsix installation failed. RC: {process.returncode}, STDOUT: {process.stdout.strip()}, STDERR: {process.stderr.strip()}'
                    )
    except (FileNotFoundError, TypeError, Exception) as e:
        logger.info(
            f"Could not locate/process bundled .vsix ('{vsix_filename}'): {e}. Proceeding to Marketplace attempt."
        )

    # Attempt 2: Install from Marketplace (if bundled failed or wasn't found)
    if not installation_successful_message_shown:
        try:
            process = subprocess.run(
                [editor_command, '--install-extension', extension_id, '--force'],
                capture_output=True,
                text=True,
                check=False,
            )
            install_command_executed = True
            if process.returncode == 0:
                print(
                    f'INFO: OpenHands {editor_name} extension installed successfully (from Marketplace: {extension_id}).'
                )
                print(
                    f'      Please reload {editor_name} if prompted to activate the extension.'
                )
                installation_successful_message_shown = True
            else:
                # This is a common failure point if command is fine but install fails (e.g. user cancels prompt)
                print(
                    f'INFO: Attempted to install OpenHands {editor_name} extension, but it may require your confirmation in {editor_name} or encountered an issue.'
                )
                print(
                    f"      If not installed, search for '{extension_id}' in the {editor_name} Marketplace."
                )
                logger.warning(
                    f"Marketplace installation for '{extension_id}' failed. RC: {process.returncode}, STDOUT: {process.stdout.strip()}, STDERR: {process.stderr.strip()}"
                )

        except FileNotFoundError:
            print(
                f"INFO: To complete {editor_name} integration, please ensure the '{editor_command}' command-line tool is in your PATH and restart OpenHands,"
            )
            print(
                f"      or install the '{extension_id}' extension manually from the {editor_name} Marketplace."
            )
            install_command_executed = False  # command itself failed
        except Exception as e:
            print(
                f'INFO: An unexpected error occurred while trying to install the {editor_name} extension: {e}'
            )
            print(
                f"      Please try installing '{extension_id}' manually from the {editor_name} Marketplace."
            )
            install_command_executed = False

    # Final messages based on whether any command was run
    if not install_command_executed and not installation_successful_message_shown:
        # This case means command was not found, and no prior success.
        pass  # The FileNotFoundError message above is sufficient.
    elif install_command_executed and not installation_successful_message_shown:
        # Means command ran but didn't result in a success message (e.g. user cancelled, other error)
        # The messages printed during the marketplace attempt should cover this.
        pass

    try:
        flag_file.touch()  # Mark that an attempt (successful or not) was made
    except OSError as e:
        logger.warning(
            f'Could not create {editor_name} extension attempt flag file: {e}'
        )
