#!/usr/bin/env python3
"""Simple script to test if setup script is executed multiple times."""

import sys

sys.path.insert(0, '/workspace/OpenHands')

# Let's examine the maybe_run_setup_script method to understand the issue
from openhands.runtime.base import Runtime


def analyze_setup_script_method():
    """Analyze the maybe_run_setup_script method to understand potential duplicate execution."""

    # Let's look at the source code of the method
    import inspect

    print('=== Analyzing maybe_run_setup_script method ===')
    print(inspect.getsource(Runtime.maybe_run_setup_script))

    print('\n=== Analysis ===')
    print('Looking at the method, we need to check:')
    print('1. Does it have any protection against multiple executions?')
    print('2. Does it track if the setup script has already been run?')
    print('3. Are there any flags or state variables to prevent re-execution?')


if __name__ == '__main__':
    analyze_setup_script_method()
