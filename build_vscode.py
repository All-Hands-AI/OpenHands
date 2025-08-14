import os
import pathlib
import subprocess

# This script is intended to be run by Poetry during the build process.

# Define the expected name of the .vsix file based on the extension's package.json
# This should match the name and version in openhands-vscode/package.json
EXTENSION_NAME = 'openhands-vscode'
EXTENSION_VERSION = '0.0.1'
VSIX_FILENAME = f'{EXTENSION_NAME}-{EXTENSION_VERSION}.vsix'

# Paths
ROOT_DIR = pathlib.Path(__file__).parent.resolve()
VSCODE_EXTENSION_DIR = ROOT_DIR / 'openhands' / 'integrations' / 'vscode'


def check_node_version():
    """Check if Node.js version is sufficient for building the extension."""
    try:
        result = subprocess.run(
            ['node', '--version'], capture_output=True, text=True, check=True
        )
        version_str = result.stdout.strip()
        # Extract major version number (e.g., "v12.22.9" -> 12)
        major_version = int(version_str.lstrip('v').split('.')[0])
        return major_version >= 18  # Align with frontend actual usage (18.20.1)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False


def build_vscode_extension():
    """Builds the VS Code extension."""
    vsix_path = VSCODE_EXTENSION_DIR / VSIX_FILENAME

    # Check if VSCode extension build is disabled via environment variable
    if os.environ.get('SKIP_VSCODE_BUILD', '').lower() in ('1', 'true', 'yes'):
        print('--- Skipping VS Code extension build (SKIP_VSCODE_BUILD is set) ---')
        if vsix_path.exists():
            print(f'--- Using existing VS Code extension: {vsix_path} ---')
        else:
            print('--- No pre-built VS Code extension found ---')
        return

    # Check Node.js version - if insufficient, use pre-built extension as fallback
    if not check_node_version():
        print('--- Warning: Node.js version < 18 detected or Node.js not found ---')
        print('--- Skipping VS Code extension build (requires Node.js >= 18) ---')
        print('--- Using pre-built extension if available ---')

        if not vsix_path.exists():
            print('--- Warning: No pre-built VS Code extension found ---')
            print('--- VS Code extension will not be available ---')
        else:
            print(f'--- Using pre-built VS Code extension: {vsix_path} ---')
        return

    print(f'--- Building VS Code extension in {VSCODE_EXTENSION_DIR} ---')

    try:
        # Ensure npm dependencies are installed
        print('--- Running npm install for VS Code extension ---')
        subprocess.run(
            ['npm', 'install'],
            cwd=VSCODE_EXTENSION_DIR,
            check=True,
            shell=os.name == 'nt',
        )

        # Package the extension
        print(f'--- Packaging VS Code extension ({VSIX_FILENAME}) ---')
        subprocess.run(
            ['npm', 'run', 'package-vsix'],
            cwd=VSCODE_EXTENSION_DIR,
            check=True,
            shell=os.name == 'nt',
        )

        # Verify the generated .vsix file exists
        if not vsix_path.exists():
            raise FileNotFoundError(
                f'VS Code extension package not found after build: {vsix_path}'
            )

        print(f'--- VS Code extension built successfully: {vsix_path} ---')

    except subprocess.CalledProcessError as e:
        print(f'--- Warning: Failed to build VS Code extension: {e} ---')
        print('--- Continuing without building extension ---')
        if not vsix_path.exists():
            print('--- Warning: No pre-built VS Code extension found ---')
            print('--- VS Code extension will not be available ---')


def build(setup_kwargs):
    """
    This function is called by Poetry during the build process.
    `setup_kwargs` is a dictionary that will be passed to `setuptools.setup()`.
    """
    print('--- Running custom Poetry build script (build_vscode.py) ---')

    # Build the VS Code extension and place the .vsix file
    build_vscode_extension()

    # Poetry will handle including files based on pyproject.toml `include` patterns.
    # Ensure openhands/integrations/vscode/*.vsix is included there.

    print('--- Custom Poetry build script (build_vscode.py) finished ---')


if __name__ == '__main__':
    print('Running build_vscode.py directly for testing VS Code extension packaging...')
    build_vscode_extension()
    print('Direct execution of build_vscode.py finished.')
