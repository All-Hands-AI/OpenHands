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
    """Attempt to install the OpenHands editor extension with verification and retry.

    Improvements over the previous approach:
    - Verifies actual installation via the editor CLI before/after attempts
    - Tracks attempt timestamps and uses exponential backoff between retries
    - Distinguishes permanent failures (e.g., command not found) from transient ones
    - Supports multiple editor variants (e.g., VS Code stable and insiders)
    - Allows user reset via OPENHANDS_RESET_VSCODE=1

    Status file format (first use creates ~/.openhands/.editor_extension_status.json):
    {
      "vscode": {
        "attempts": 2,
        "last_attempt": "2025-08-14T05:12:00Z",
        "last_success": "2025-08-14T05:15:26Z",
        "permanent_failure": null
      },
      "windsurf": {
        "attempts": 1,
        "last_attempt": "2025-08-13T02:01:00Z",
        "last_success": null,
        "permanent_failure": "command_not_found"
      }
    }
    """
    # Check if we are in a supported editor environment
    is_vscode_like = os.environ.get('TERM_PROGRAM') == 'vscode'
    is_windsurf = (
        os.environ.get('__CFBundleIdentifier') == 'com.exafunction.windsurf'
        or 'windsurf' in os.environ.get('PATH', '').lower()
        or any(
            isinstance(val, str) and 'windsurf' in val.lower()
            for val in os.environ.values()
        )
    )
    if not (is_vscode_like or is_windsurf):
        return

    # Determine editor context and candidate commands
    editor_key = 'windsurf' if is_windsurf else 'vscode'
    editor_name = 'Windsurf' if is_windsurf else 'VS Code'
    candidate_commands = ['surf'] if is_windsurf else ['code', 'code-insiders']

    flag_dir = pathlib.Path.home() / '.openhands'
    status_file = flag_dir / '.editor_extension_status.json'
    legacy_flag_file = flag_dir / f'.{editor_key}_extension_installed'
    extension_id = 'openhands.openhands-vscode'

    try:
        flag_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.debug(f'Could not ensure status directory exists: {e}')
        return

    # Load status and optionally reset
    status = {}
    try:
        if status_file.exists():
            status = json.loads(status_file.read_text())
    except Exception as e:
        logger.debug(f'Could not read status file: {e}')
        status = {}

    if os.environ.get('OPENHANDS_RESET_VSCODE') == '1':
        status.pop(editor_key, None)
        try:
            status_file.write_text(json.dumps(status))
        except Exception:
            pass

    entry = status.get(editor_key, {})

    # If legacy success flag exists, respect it but verify installation anyway
    if legacy_flag_file.exists():
        # If actually installed, keep and exit
        if _is_extension_installed_by_any(candidate_commands, extension_id):
            return
        else:
            # Legacy flag exists but extension missing; remove the flag and continue
            try:
                legacy_flag_file.unlink(missing_ok=True)
            except Exception:
                pass

    # If already installed (any variant), mark success and exit
    if _is_extension_installed_by_any(candidate_commands, extension_id):
        _mark_installation_successful(legacy_flag_file, editor_name)
        # Update status
        entry.update({'last_success': _now_iso(), 'permanent_failure': None})
        status[editor_key] = entry
        _save_status(status_file, status)
        print(f'INFO: OpenHands {editor_name} extension is already installed.')
        return

    # Decide if we should attempt now based on backoff
    attempts = int(entry.get('attempts', 0) or 0)
    last_attempt = entry.get('last_attempt')
    permanent_failure = entry.get('permanent_failure')

    if permanent_failure:
        # Don't spam attempts if we know it cannot work without user action
        print(
            f'INFO: Skipping automatic {editor_name} extension install (permanent failure: {permanent_failure}).\n'
            '      See docs to resolve or set OPENHANDS_RESET_VSCODE=1 to retry.'
        )
        return

    if last_attempt:
        wait_seconds = _calc_backoff_seconds(max(1, attempts))
        if not _elapsed_enough(last_attempt, wait_seconds):
            remaining = int(_remaining_seconds(last_attempt, wait_seconds))
            hrs = max(1, remaining // 3600)
            print(
                f'INFO: Previous {editor_name} extension install attempt failed. Will retry later (~{hrs}h).\n'
                '      Set OPENHANDS_RESET_VSCODE=1 to force retry sooner.'
            )
            return

    # Prepare available editor commands
    available = _available_commands(candidate_commands)
    if not available:
        # Permanent failure: no editor CLI found
        entry.update(
            {
                'attempts': attempts + 1,
                'last_attempt': _now_iso(),
                'permanent_failure': 'command_not_found',
            }
        )
        status[editor_key] = entry
        _save_status(status_file, status)
        print(
            f'INFO: Cannot auto-install {editor_name} extension: no editor CLI found in PATH.\n'
            f'      Tried commands: {", ".join(candidate_commands)}.\n'
            f'      Install the editor CLI or install the extension manually (Extensions: Install from VSIX).'
        )
        return

    editor_command = available[0]  # Prefer the first available variant

    print(
        f'INFO: Attempting to install the OpenHands {editor_name} extension (via {editor_command})...'
    )

    entry.update({'attempts': attempts + 1, 'last_attempt': _now_iso()})

    # Attempt 1: bundled VSIX
    try:
        if _attempt_bundled_install(editor_command, editor_name):
            _mark_installation_successful(legacy_flag_file, editor_name)
            entry.update({'last_success': _now_iso(), 'permanent_failure': None})
            status[editor_key] = entry
            _save_status(status_file, status)
            return
    except FileNotFoundError:
        # Permanent failure for this environment until user fixes PATH
        entry.update({'permanent_failure': 'command_not_found'})
        status[editor_key] = entry
        _save_status(status_file, status)
        print(
            f"INFO: '{editor_command}' not found. Please add it to PATH or install the extension manually."
        )
        return
    except Exception as e:
        logger.debug(f'Bundled install attempt error: {e}')

    # Attempt 2: GitHub Releases
    github_ok = False
    try:
        github_ok = _attempt_github_install(editor_command, editor_name)
    except FileNotFoundError:
        entry.update({'permanent_failure': 'command_not_found'})
        status[editor_key] = entry
        _save_status(status_file, status)
        print(
            f"INFO: '{editor_command}' not found. Please add it to PATH or install the extension manually."
        )
        return
    except Exception as e:
        logger.debug(f'GitHub install attempt error: {e}')

    if github_ok:
        _mark_installation_successful(legacy_flag_file, editor_name)
        entry.update({'last_success': _now_iso(), 'permanent_failure': None})
        status[editor_key] = entry
        _save_status(status_file, status)
        return

    # If all attempts failed, inform the user (transient failure)
    status[editor_key] = entry
    _save_status(status_file, status)
    print('INFO: Automatic installation failed. Please install manually if needed.')
    print(
        f'INFO: Will retry installation later based on backoff policy for {editor_name}.'
    )


def _save_status(path: pathlib.Path, data: dict) -> None:
    try:
        path.write_text(json.dumps(data))
    except Exception as e:
        logger.debug(f'Could not write status file: {e}')


def _now_iso() -> str:
    import datetime as _dt

    return _dt.datetime.utcnow().isoformat() + 'Z'


def _elapsed_enough(since_iso: str, wait_seconds: int) -> bool:
    import datetime as _dt

    try:
        t = _dt.datetime.fromisoformat(since_iso.replace('Z', ''))
    except Exception:
        return True
    return (_dt.datetime.utcnow() - t).total_seconds() >= wait_seconds


def _remaining_seconds(since_iso: str, wait_seconds: int) -> int:
    import datetime as _dt

    try:
        t = _dt.datetime.fromisoformat(since_iso.replace('Z', ''))
    except Exception:
        return 0
    elapsed = (_dt.datetime.utcnow() - t).total_seconds()
    return max(0, int(wait_seconds - elapsed))


def _calc_backoff_seconds(attempts: int) -> int:
    # Start with 24 hours and exponentially back off, capped at 72 hours
    base = 24 * 3600
    return min(72 * 3600, base * (2 ** max(0, attempts - 1)))


def _available_commands(candidates: list[str]) -> list[str]:
    available: list[str] = []
    for c in candidates:
        try:
            proc = subprocess.run([c, '--version'], capture_output=True, text=True)
            if proc.returncode == 0:
                available.append(c)
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return available


def _is_extension_installed_by_any(commands: list[str], extension_id: str) -> bool:
    """Check if the extension is installed using any of the provided editor commands.

    Args:
        commands: A list of editor command names to check (e.g., ['code', 'windsurf']).
        extension_id: The extension ID to check for.

    Returns:
        bool: True if the extension is installed by any of the commands, False otherwise.
    """
    for cmd in _available_commands(commands):
        if _is_extension_installed(cmd, extension_id):
            return True
    return False


def _mark_installation_successful(flag_file: pathlib.Path, editor_name: str) -> None:
    """Mark the extension installation as successful by creating the flag file.

    Args:
        flag_file: Path to the flag file to create
        editor_name: Human-readable name of the editor for logging
    """
    try:
        flag_file.touch()
        logger.debug(f'{editor_name} extension installation marked as successful.')
    except OSError as e:
        logger.debug(f'Could not create {editor_name} extension success flag file: {e}')


def _is_extension_installed(editor_command: str, extension_id: str) -> bool:
    """Check if the OpenHands extension is already installed.

    Args:
        editor_command: The command to run the editor (e.g., 'code', 'windsurf')
        extension_id: The extension ID to check for

    Returns:
        bool: True if extension is already installed, False otherwise
    """
    try:
        process = subprocess.run(
            [editor_command, '--list-extensions'],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode == 0:
            installed_extensions = process.stdout.strip().split('\n')
            return extension_id in installed_extensions
    except Exception as e:
        logger.debug(f'Could not check installed extensions: {e}')

    return False


def _attempt_github_install(editor_command: str, editor_name: str) -> bool:
    """Attempt to install the extension from GitHub Releases.

    Downloads the latest VSIX file from GitHub releases and attempts to install it.
    Ensures proper cleanup of temporary files.

    Args:
        editor_command: The command to run the editor (e.g., 'code', 'windsurf')
        editor_name: Human-readable name of the editor (e.g., 'VS Code', 'Windsurf')

    Returns:
        bool: True if installation succeeded, False otherwise
    """
    vsix_path_from_github = download_latest_vsix_from_github()
    if not vsix_path_from_github:
        return False

    github_success = False
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
            github_success = True
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

    return github_success


def _attempt_bundled_install(editor_command: str, editor_name: str) -> bool:
    """Attempt to install the extension from the bundled VSIX file.

    Uses the VSIX file packaged with the OpenHands installation.

    Args:
        editor_command: The command to run the editor (e.g., 'code', 'windsurf')
        editor_name: Human-readable name of the editor (e.g., 'VS Code', 'Windsurf')

    Returns:
        bool: True if installation succeeded, False otherwise
    """
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
                    return True
                else:
                    logger.debug(
                        f'Bundled .vsix installation failed: {process.stderr.strip()}'
                    )
            else:
                logger.debug(f'Bundled .vsix not found at {vsix_path}.')
    except Exception as e:
        logger.warning(
            f'Could not auto-install extension. Please make sure "code" command is in PATH. Error: {e}'
        )

    return False


def _attempt_marketplace_install(
    editor_command: str, editor_name: str, extension_id: str
) -> bool:
    """Attempt to install the extension from the marketplace.

    This method is currently unused as the OpenHands extension is not yet published
    to the VS Code/Windsurf marketplace. It's kept here for future use when the
    extension becomes available.

    Args:
        editor_command: The command to use ('code' or 'surf')
        editor_name: Human-readable editor name ('VS Code' or 'Windsurf')
        extension_id: The extension ID to install

    Returns:
        True if installation succeeded, False otherwise
    """
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
            return True
        else:
            logger.debug(f'Marketplace installation failed: {process.stderr.strip()}')
            return False
    except FileNotFoundError:
        print(
            f"INFO: To complete {editor_name} integration, please ensure the '{editor_command}' command-line tool is in your PATH."
        )
        return False
    except Exception as e:
        logger.debug(
            f'An unexpected error occurred trying to install from the Marketplace: {e}'
        )
        return False
