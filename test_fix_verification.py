#!/usr/bin/env python3
"""Simple script to verify the duplicate execution fix."""

import sys

sys.path.insert(0, '/workspace/OpenHands')


def test_fix():
    """Test that the fix prevents duplicate execution."""

    # Import the Runtime class
    from openhands.runtime.base import Runtime

    print('=== Testing the duplicate execution fix ===')

    # Check that the _setup_script_executed attribute exists
    print(
        f'Runtime class has _setup_script_executed attribute: {hasattr(Runtime, "_setup_script_executed")}'
    )

    # Check the default value
    print(f'Default value of _setup_script_executed: {Runtime._setup_script_executed}')

    # Let's examine the updated maybe_run_setup_script method
    import inspect

    source = inspect.getsource(Runtime.maybe_run_setup_script)

    print('\n=== Updated maybe_run_setup_script method ===')
    print(source)

    print('\n=== Analysis ===')
    if 'if self._setup_script_executed:' in source:
        print('✅ Fix implemented: Method checks _setup_script_executed flag')
    else:
        print('❌ Fix not found: Method does not check _setup_script_executed flag')

    if 'self._setup_script_executed = True' in source:
        print('✅ Fix implemented: Method sets _setup_script_executed flag')
    else:
        print('❌ Fix not found: Method does not set _setup_script_executed flag')

    print('\n=== Summary ===')
    print('The fix should prevent duplicate execution by:')
    print('1. Checking if _setup_script_executed is True at the start')
    print('2. Returning early if the script has already been executed')
    print('3. Setting _setup_script_executed = True after execution')


if __name__ == '__main__':
    test_fix()
