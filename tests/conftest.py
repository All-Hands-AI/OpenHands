"""Pytest bootstrap to ensure repo source takes precedence over any preinstalled
OpenHands copy in CI environments where /openhands/code may precede the repo
on sys.path.

This avoids shadowing new subpackages like `openhands.conversation`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Insert repository root at the front of sys.path if not already there
REPO_ROOT = Path(__file__).resolve().parents[1]
repo_str = str(REPO_ROOT)
if sys.path[0] != repo_str:
    try:
        sys.path.remove(repo_str)
    except ValueError:
        pass
    sys.path.insert(0, repo_str)
