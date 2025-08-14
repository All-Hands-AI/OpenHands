# Ensure local repository code takes precedence over any pre-installed OpenHands code
# Some CI environments add /openhands/code to sys.path which may contain an older
# copy of the OpenHands package. This file is auto-imported by Python (via site)
# and reorders sys.path so that the current working directory (the repo) is preferred.
import os
import sys
from pathlib import Path

try:
    here = Path(__file__).resolve().parent
    repo_pkg = here / 'openhands'
    preinstalled_dir = Path('/openhands/code')

    if repo_pkg.exists() and preinstalled_dir.exists():
        # Move current repo path ("here") to the front of sys.path, ahead of /openhands/code
        # Remove any existing occurrences to avoid duplicates
        sys.path[:] = [p for p in sys.path if p != str(here)]
        sys.path.insert(0, str(here))

        # If openhands is already imported from a preinstalled location, reload from the repo
        m = sys.modules.get('openhands')
        if m is not None and getattr(m, '__file__', '') and str(preinstalled_dir) in m.__file__:
            # Drop the cached package so subsequent imports come from the repo
            for k in list(sys.modules.keys()):
                if k == 'openhands' or k.startswith('openhands.'):
                    sys.modules.pop(k, None)
except Exception:
    # Never block interpreter startup
    pass
