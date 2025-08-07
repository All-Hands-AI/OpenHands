import os
import pathlib
import subprocess

# This script is intended to be run by Poetry during the build process.
# It builds the VS Code extension, but intelligently skips the build in contexts
# where it's not needed (CLI-only installations, shallow repositories, etc.)
#
# Environment variables that control behavior:
# - SKIP_VSCODE_BUILD=1: Explicitly skip VS Code extension build
# - BUILD_VSCODE_IN_CI=1: Force build in CI environments (default: skip in CI)
#
# The script automatically detects and skips building in these scenarios:
# - CLI-only installation contexts (uvx, pipx, uv)
# - Shallow git repositories (common with package managers)
# - Git repositories with invalid HEAD (empty repos, etc.)
# - CI/automated environments (unless BUILD_VSCODE_IN_CI=1)
# - Missing or insufficient Node.js version

# Define the expected name of the .vsix file based on the extension's package.json
# This should match the name and version in openhands-vscode/package.json
EXTENSION_NAME = 'openhands-vscode'
EXTENSION_VERSION = '0.0.1'
VSIX_FILENAME = f'{EXTENSION_NAME}-{EXTENSION_VERSION}.vsix'

# Paths
ROOT_DIR = pathlib.Path(__file__).parent.resolve()
VSCODE_EXTENSION_DIR = ROOT_DIR / 'openhands' / 'integrations' / 'vscode'


def check_git_repository_state():
    """Check if we're in a valid git repository and can access HEAD."""
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            timeout=10,
        )
        if result.returncode != 0:
            return False, 'Not in a git repository'

        # Check if HEAD exists and is valid
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            timeout=10,
        )
        if result.returncode != 0:
            return False, f'Cannot resolve HEAD: {result.stderr.strip()}'

        # Check if it's a shallow repository
        shallow_file = pathlib.Path(result.stdout.strip()) / '.git' / 'shallow'
        if not shallow_file.exists():
            # Alternative check for shallow repo
            result = subprocess.run(
                ['git', 'rev-parse', '--is-shallow-repository'],
                capture_output=True,
                text=True,
                cwd=ROOT_DIR,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip() == 'true':
                return True, 'Shallow repository detected'
        else:
            return True, 'Shallow repository detected'

        return True, 'Valid git repository'

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as e:
        return False, f'Git check failed: {str(e)}'


def check_node_version():
    """Check if Node.js version is sufficient for building the extension."""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        version_str = result.stdout.strip()
        # Extract major version number (e.g., "v12.22.9" -> 12)
        major_version = int(version_str.lstrip('v').split('.')[0])
        return major_version >= 18  # Align with frontend actual usage (18.20.1)
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        ValueError,
    ):
        return False


def should_build_vscode_extension():
    """Determine if VS Code extension should be built based on context."""
    # Check if explicitly disabled
    if os.environ.get('SKIP_VSCODE_BUILD', '').lower() in ('1', 'true', 'yes'):
        return False, 'SKIP_VSCODE_BUILD environment variable is set'

    # Check if we're being installed via uvx or similar tools (CLI-only context)
    # These tools typically set specific environment variables or have specific parent processes
    cli_only_indicators = [
        'UVX_PROJECT',
        'PIPX_HOME',
        'PIP_DISABLE_PIP_VERSION_CHECK',
        'UV_PROJECT_ENVIRONMENT',
        'UV_CACHE_DIR',  # uv/uvx specific
    ]
    if any(env_var in os.environ for env_var in cli_only_indicators):
        return False, 'Detected CLI-only installation context (uvx/pipx/uv)'

    # Check if parent process suggests CLI-only installation
    try:
        import psutil

        current_process = psutil.Process()
        parent_process = current_process.parent()
        if parent_process and any(
            name in parent_process.name().lower() for name in ['uvx', 'pipx', 'uv']
        ):
            return False, f'Detected CLI-only installation via {parent_process.name()}'
    except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
        # psutil not available or can't access parent process info
        pass

    # Check if we're in a CI/automated environment where VS Code extension isn't needed
    if any(
        env_var in os.environ
        for env_var in ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL']
    ):
        # Allow override for CI that specifically wants to build the extension
        if os.environ.get('BUILD_VSCODE_IN_CI', '').lower() not in ('1', 'true', 'yes'):
            return (
                False,
                'Detected CI environment, skipping VS Code build (set BUILD_VSCODE_IN_CI=1 to override)',
            )

    # Check if we're in a development environment (has .git and not shallow)
    git_valid, git_msg = check_git_repository_state()
    if not git_valid:
        return False, f'Git repository issues: {git_msg}'

    if 'shallow' in git_msg.lower():
        return (
            False,
            'Shallow repository detected, skipping VS Code build to avoid issues',
        )

    return True, 'Development environment detected, building VS Code extension'


def build_vscode_extension():
    """Builds the VS Code extension."""
    vsix_path = VSCODE_EXTENSION_DIR / VSIX_FILENAME

    # Check if we should build the VS Code extension based on context
    should_build, reason = should_build_vscode_extension()
    if not should_build:
        print(f'--- Skipping VS Code extension build: {reason} ---')
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
            timeout=300,  # 5 minute timeout
        )

        # Package the extension
        print(f'--- Packaging VS Code extension ({VSIX_FILENAME}) ---')
        subprocess.run(
            ['npm', 'run', 'package-vsix'],
            cwd=VSCODE_EXTENSION_DIR,
            check=True,
            shell=os.name == 'nt',
            timeout=300,  # 5 minute timeout
        )

        # Verify the generated .vsix file exists
        if not vsix_path.exists():
            raise FileNotFoundError(
                f'VS Code extension package not found after build: {vsix_path}'
            )

        print(f'--- VS Code extension built successfully: {vsix_path} ---')

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
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
