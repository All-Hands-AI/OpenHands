#!/usr/bin/env python3
"""
Script to verify that the current pyproject.toml has all the same packages as main branch,
just organized into different groups.
"""

import sys
from pathlib import Path

import toml


def extract_all_dependencies(pyproject_data):
    """Extract all dependencies from a pyproject.toml data structure."""
    deps = set()

    # Main dependencies
    main_deps = pyproject_data.get('tool', {}).get('poetry', {}).get('dependencies', {})
    for name, spec in main_deps.items():
        if name != 'python':  # Skip python version constraint
            # Handle both string and dict specs
            if isinstance(spec, dict):
                if not spec.get(
                    'optional', False
                ):  # Only count non-optional deps for main
                    deps.add(name)
            else:
                deps.add(name)

    # Group dependencies
    groups = pyproject_data.get('tool', {}).get('poetry', {}).get('group', {})
    for group_name, group_data in groups.items():
        if not group_data.get('optional', True):  # Only count non-optional groups
            group_deps = group_data.get('dependencies', {})
            for name in group_deps:
                deps.add(name)

    return deps


def extract_all_dependencies_including_optional(pyproject_data):
    """Extract ALL dependencies including optional ones."""
    deps = set()

    # Main dependencies (including optional)
    main_deps = pyproject_data.get('tool', {}).get('poetry', {}).get('dependencies', {})
    for name, spec in main_deps.items():
        if name != 'python':  # Skip python version constraint
            deps.add(name)

    # Group dependencies
    groups = pyproject_data.get('tool', {}).get('poetry', {}).get('group', {})
    for group_name, group_data in groups.items():
        group_deps = group_data.get('dependencies', {})
        for name in group_deps:
            deps.add(name)

    return deps


def main():
    # Load current pyproject.toml
    current_path = Path('pyproject.toml')
    with open(current_path) as f:
        current_data = toml.load(f)

    # Load main branch pyproject.toml
    main_path = Path('/tmp/main_pyproject.toml')
    with open(main_path) as f:
        main_data = toml.load(f)

    # Extract dependencies
    current_deps = extract_all_dependencies_including_optional(current_data)
    main_deps = extract_all_dependencies_including_optional(main_data)

    print('=== Dependency Comparison ===')
    print(f'Main branch dependencies: {len(main_deps)}')
    print(f'Current branch dependencies: {len(current_deps)}')

    # Find differences
    missing_in_current = main_deps - current_deps
    extra_in_current = current_deps - main_deps

    if missing_in_current:
        print(f'\n❌ Missing in current ({len(missing_in_current)}):')
        for dep in sorted(missing_in_current):
            print(f'  - {dep}')

    if extra_in_current:
        print(f'\n➕ Extra in current ({len(extra_in_current)}):')
        for dep in sorted(extra_in_current):
            print(f'  - {dep}')

    if not missing_in_current and not extra_in_current:
        print('\n✅ All dependencies match!')
        return 0
    else:
        print("\n❌ Dependencies don't match!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
