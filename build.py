import os
import shutil
import subprocess
import pathlib

# This script is intended to be run by Poetry during the build process.

# Define the expected name of the .vsix file based on the extension's package.json
# This should match the name and version in openhands-vscode/package.json
EXTENSION_NAME = "openhands-vscode"
EXTENSION_VERSION = "0.0.1"
VSIX_FILENAME = f"{EXTENSION_NAME}-{EXTENSION_VERSION}.vsix"

# Paths
ROOT_DIR = pathlib.Path(__file__).parent.resolve()
VSCODE_EXTENSION_DIR = ROOT_DIR / "openhands-vscode"
RESOURCES_DIR = ROOT_DIR / "openhands" / "resources" # Target for the .vsix

def build_vscode_extension():
    """Builds the VS Code extension and copies the .vsix file."""
    print(f"--- Building VS Code extension in {VSCODE_EXTENSION_DIR} ---")

    # Ensure npm dependencies are installed
    print("--- Running npm install for VS Code extension ---")
    subprocess.run(["npm", "install"], cwd=VSCODE_EXTENSION_DIR, check=True, shell=os.name == 'nt')

    # Package the extension
    print(f"--- Packaging VS Code extension ({VSIX_FILENAME}) ---")
    subprocess.run(["npm", "run", "package-vsix"], cwd=VSCODE_EXTENSION_DIR, check=True, shell=os.name == 'nt')

    # Source path of the generated .vsix file
    vsix_source_path = VSCODE_EXTENSION_DIR / VSIX_FILENAME

    if not vsix_source_path.exists():
        raise FileNotFoundError(
            f"VS Code extension package not found after build: {vsix_source_path}"
        )

    # Ensure the target resources directory exists
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    # Destination path for the .vsix file
    vsix_dest_path = RESOURCES_DIR / VSIX_FILENAME

    print(f"--- Copying {vsix_source_path} to {vsix_dest_path} ---")
    shutil.copy(vsix_source_path, vsix_dest_path)
    print(f"--- Copied {VSIX_FILENAME} successfully ---")

def build(setup_kwargs):
    """
    This function is called by Poetry during the build process.
    `setup_kwargs` is a dictionary that will be passed to `setuptools.setup()`.
    """
    print("--- Running custom Poetry build script (build.py) ---")

    # Build the VS Code extension and place the .vsix file
    build_vscode_extension()

    # Poetry will handle including files based on pyproject.toml `include` patterns.
    # Ensure openhands/resources/*.vsix is included there.

    print("--- Custom Poetry build script (build.py) finished ---")

if __name__ == "__main__":
    # This allows running the script directly for testing, if needed.
    print("Running build.py directly for testing VS Code extension packaging...")
    build_vscode_extension()
    print("Direct execution of build.py finished.")
