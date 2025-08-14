#!/usr/bin/env python3

import toml


def parse_dependencies(pyproject_path):
    """Parse dependencies from pyproject.toml"""
    with open(pyproject_path, 'r') as f:
        data = toml.load(f)

    deps = data['tool']['poetry']['dependencies']
    required = {}
    optional = {}

    for name, spec in deps.items():
        if name == 'python':
            continue

        if isinstance(spec, dict) and spec.get('optional', False):
            optional[name] = spec
        else:
            required[name] = spec

    return required, optional


def main():
    # Parse main branch dependencies
    main_required, main_optional = parse_dependencies('/tmp/main_pyproject.toml')

    # Parse current branch dependencies
    current_required, current_optional = parse_dependencies('pyproject.toml')

    print('=== Dependencies that were required in main but optional in current ===')
    made_optional = []
    for name in main_required:
        if name in current_optional:
            made_optional.append(name)
            print(f'  - {name}')

    print(f'\nTotal: {len(made_optional)} dependencies made optional')

    print('\n=== Dependencies that were optional in main but required in current ===')
    made_required = []
    for name in main_optional:
        if name in current_required:
            made_required.append(name)
            print(f'  - {name}')

    print(f'\nTotal: {len(made_required)} dependencies made required')

    return made_optional, made_required


if __name__ == '__main__':
    main()
