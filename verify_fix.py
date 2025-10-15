#!/usr/bin/env python3
"""
Simple verification script to check if the recursion fix is properly applied.
"""

import os
import sys


def check_fix():
    """Check if the recursion fix is properly applied."""
    print('🔍 Checking if recursion fix is applied...')

    # Check if the file exists
    llm_file = 'openhands/llm/llm.py'
    if not os.path.exists(llm_file):
        print(f'❌ File not found: {llm_file}')
        return False

    # Read the file content
    with open(llm_file, 'r') as f:
        content = f.read()

    # Check for the fix
    if 'resp = self._completion_unwrapped(*args, **kwargs)' in content:
        print('✅ Recursion fix is properly applied!')
        print('✅ Found: resp = self._completion_unwrapped(*args, **kwargs)')

        # Also check that the old problematic line is not present
        if 'resp = self._completion(*args, **kwargs)' not in content:
            print('✅ Old problematic line is not present')
            return True
        else:
            print('⚠️  Warning: Old problematic line still present')
            return False
    else:
        print('❌ Recursion fix is NOT applied!')
        print('❌ Expected to find: resp = self._completion_unwrapped(*args, **kwargs)')

        # Check if the old problematic line is present
        if 'resp = self._completion(*args, **kwargs)' in content:
            print(
                '❌ Found old problematic line: resp = self._completion(*args, **kwargs)'
            )

        return False


def check_git_status():
    """Check git status to see if user is on the right branch."""
    print('\n🔍 Checking git status...')

    try:
        import subprocess

        result = subprocess.run(
            ['git', 'branch', '--show-current'], capture_output=True, text=True, cwd='.'
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            print(f'📍 Current branch: {branch}')

            if branch == 'openhands/add-gpt-5-codex-support':
                print('✅ On the correct branch')

                # Check if there are uncommitted changes
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    capture_output=True,
                    text=True,
                    cwd='.',
                )
                if result.returncode == 0:
                    if result.stdout.strip():
                        print('⚠️  There are uncommitted changes')
                        print(
                            '💡 Consider running: git stash or git add . && git commit'
                        )
                    else:
                        print('✅ No uncommitted changes')

                # Check latest commit
                result = subprocess.run(
                    ['git', 'log', '--oneline', '-1'],
                    capture_output=True,
                    text=True,
                    cwd='.',
                )
                if result.returncode == 0:
                    commit = result.stdout.strip()
                    print(f'📝 Latest commit: {commit}')

                    if 'Fix recursion issue by using _completion_unwrapped' in commit:
                        print('✅ Latest commit contains the recursion fix')
                        return True
                    else:
                        print('❌ Latest commit does not contain the recursion fix')
                        print(
                            '💡 Try: git pull origin openhands/add-gpt-5-codex-support'
                        )
                        return False
            else:
                print('❌ Wrong branch. Expected: openhands/add-gpt-5-codex-support')
                print('💡 Try: git checkout openhands/add-gpt-5-codex-support')
                return False
        else:
            print('❌ Could not determine git branch')
            return False
    except Exception as e:
        print(f'❌ Error checking git status: {e}')
        return False


def main():
    print('=' * 60)
    print('🔧 RECURSION FIX VERIFICATION')
    print('=' * 60)

    fix_applied = check_fix()
    git_ok = check_git_status()

    print('\n' + '=' * 60)
    print('📋 VERIFICATION SUMMARY')
    print('=' * 60)

    if fix_applied and git_ok:
        print('🎉 ALL CHECKS PASSED!')
        print('✅ Recursion fix is properly applied')
        print('✅ Git status is correct')
        print("\n💡 If you're still seeing recursion errors, try:")
        print('   1. Restart your Python process/server')
        print('   2. Clear any Python cache: rm -rf __pycache__ .pytest_cache')
        print('   3. Reinstall dependencies: poetry install')
        return 0
    else:
        print('❌ SOME CHECKS FAILED!')
        if not fix_applied:
            print('❌ Recursion fix is not properly applied')
        if not git_ok:
            print('❌ Git status issues detected')
        print('\n💡 Please follow the suggestions above to fix the issues.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
