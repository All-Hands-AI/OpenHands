"""Testing bootstrap to prefer repository source over pre-installed copy.

In CI, PYTHONPATH may include '/openhands/code' before the repo path, which can
shadow new subpackages. This ensures the current repository root is at the front
of sys.path so that 'import openhands' resolves to the source we are working on.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    repo_root = Path(__file__).resolve().parent
    # Put repo root at the front of sys.path, ahead of any pre-installed copies
    sys.path[:] = [str(repo_root)] + [p for p in sys.path if p and str(repo_root) != p]
except Exception:
    # Non-fatal: if anything goes wrong, leave sys.path unchanged
    pass
