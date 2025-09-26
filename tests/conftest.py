# Ensure the repository source tree is imported before any pre-installed site packages
# This avoids picking up a preinstalled OpenHands copy under /openhands/code during tests
import sys
from pathlib import Path

# tests/ -> repo root
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
