#!/usr/bin/env python3
"""
Script to extract and package the Playwright browser for use with the PyInstaller binary.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_playwright_browser_path():
    """Find the Playwright browser path in the current environment."""
    try:
        # Try to get the path from the PLAYWRIGHT_BROWSERS_PATH environment variable
        if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
            browser_path = Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])
            if browser_path.exists():
                return browser_path
        
        # Try to find it in the user's home directory
        home_dir = Path.home()
        playwright_path = home_dir / ".cache" / "ms-playwright"
        if playwright_path.exists():
            return playwright_path
        
        # Try to find it in the root user's home directory
        root_playwright_path = Path("/root/.cache/ms-playwright")
        if root_playwright_path.exists():
            return root_playwright_path
        
        # If not found, install Playwright and get the path
        print("Playwright browser not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        
        # Try again to find the path
        if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
            browser_path = Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])
            if browser_path.exists():
                return browser_path
        
        playwright_path = home_dir / ".cache" / "ms-playwright"
        if playwright_path.exists():
            return playwright_path
        
        root_playwright_path = Path("/root/.cache/ms-playwright")
        if root_playwright_path.exists():
            return root_playwright_path
        
        raise FileNotFoundError("Could not find Playwright browser path")
    except Exception as e:
        print(f"Error finding Playwright browser path: {e}")
        raise


def package_browser(output_dir):
    """Package the Playwright browser for use with the PyInstaller binary."""
    try:
        # Find the Playwright browser path
        browser_path = find_playwright_browser_path()
        print(f"Found Playwright browser at: {browser_path}")
        
        # Create the output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy the browser files
        print(f"Copying browser files to {output_path}...")
        shutil.copytree(browser_path, output_path / "ms-playwright", dirs_exist_ok=True)
        
        # Create a wrapper script for the browser
        wrapper_script = output_path / "chromium-wrapper.sh"
        with open(wrapper_script, "w") as f:
            f.write("""#!/bin/bash
# Wrapper script for Chromium

# Set up environment
export PLAYWRIGHT_BROWSERS_PATH="$(dirname "$0")/ms-playwright"

# Find the Chromium executable
CHROMIUM_PATH=$(find "$PLAYWRIGHT_BROWSERS_PATH" -name "chrome" -type f | head -n 1)

if [ -z "$CHROMIUM_PATH" ]; then
  echo "Error: Chromium executable not found in $PLAYWRIGHT_BROWSERS_PATH"
  exit 1
fi

# Execute Chromium with all arguments passed to this script
exec "$CHROMIUM_PATH" "$@"
""")
        
        # Make the wrapper script executable
        wrapper_script.chmod(0o755)
        
        print(f"Browser packaged successfully to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error packaging browser: {e}")
        raise


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./browser"
    package_browser(output_dir)