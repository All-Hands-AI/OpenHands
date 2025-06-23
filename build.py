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


def build_vscode_extension():
    """Builds the VS Code extension."""
    print(f'--- Building VS Code extension in {VSCODE_EXTENSION_DIR} ---')

    # Ensure npm dependencies are installed
    print('--- Running npm install for VS Code extension ---')
    subprocess.run(
        ['npm', 'install'], cwd=VSCODE_EXTENSION_DIR, check=True, shell=os.name == 'nt'
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
    vsix_path = VSCODE_EXTENSION_DIR / VSIX_FILENAME

    if not vsix_path.exists():
        raise FileNotFoundError(
            f'VS Code extension package not found after build: {vsix_path}'
        )

    print(f'--- VS Code extension built successfully: {vsix_path} ---')


def build(setup_kwargs):
    """
    This function is called by Poetry during the build process.
    `setup_kwargs` is a dictionary that will be passed to `setuptools.setup()`.
    """
    print('--- Running custom Poetry build script (build.py) ---')

    # Build the VS Code extension and place the .vsix file
    build_vscode_extension()

    # Poetry will handle including files based on pyproject.toml `include` patterns.
    # Ensure openhands/integrations/vscode/*.vsix is included there.

    print('--- Custom Poetry build script (build.py) finished ---')


if __name__ == '__main__':
    print('Running build.py directly for testing VS Code extension packaging...')
    build_vscode_extension()
    print('Direct execution of build.py finished.')
