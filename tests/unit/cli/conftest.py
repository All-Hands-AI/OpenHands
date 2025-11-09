import sys
from pathlib import Path

# Ensure we can import the CLI package from the repo without installing it
REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_PKG = REPO_ROOT / "openhands-cli"
if str(CLI_PKG) not in sys.path:
    sys.path.insert(0, str(CLI_PKG))
