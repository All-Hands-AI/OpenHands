#!/usr/bin/env python3
"""
Script to update the OpenAPI documentation for OpenHands.

This script generates the OpenAPI specification from the FastAPI application
and updates the documentation file at docs/openapi.json.
"""

import json
import logging
import os
import sys
import warnings
from pathlib import Path

# Suppress warnings and logs during import
logging.getLogger().setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')
os.environ['OPENHANDS_LOG_LEVEL'] = 'CRITICAL'

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from openhands import __version__
    from openhands.server.app import app
except ImportError as e:
    print(f'Error importing OpenHands modules: {e}')
    print(
        "Make sure you're running this script from the project root and dependencies are installed."
    )
    sys.exit(1)


def generate_openapi_spec():
    """Generate the OpenAPI specification from the FastAPI app."""
    return app.openapi()


def load_current_spec(spec_path):
    """Load the current OpenAPI specification if it exists."""
    if spec_path.exists():
        with open(spec_path, 'r') as f:
            return json.load(f)
    return {}


def update_openapi_spec(spec_path, backup=True):
    """Update the OpenAPI specification file."""
    # Generate new spec
    new_spec = generate_openapi_spec()

    # Load current spec for server information
    current_spec = load_current_spec(spec_path)

    # Preserve server information from current spec if it exists
    if 'servers' in current_spec:
        new_spec['servers'] = current_spec['servers']
    else:
        # Default servers if none exist
        new_spec['servers'] = [
            {'url': 'https://app.all-hands.dev', 'description': 'Production server'},
            {'url': 'http://localhost:3000', 'description': 'Local development server'},
        ]

    # Update version to match the package version
    new_spec['info']['version'] = __version__

    # Backup current file if requested
    if backup and spec_path.exists():
        backup_path = spec_path.with_suffix('.json.backup')
        spec_path.rename(backup_path)
        print(f'Backed up current spec to {backup_path}')

    # Write new spec
    with open(spec_path, 'w') as f:
        json.dump(new_spec, f, indent=2)

    return new_spec


def main():
    """Main function."""
    spec_path = project_root / 'docs' / 'openapi.json'

    print('Updating OpenAPI specification...')
    print(f'Target file: {spec_path}')

    try:
        new_spec = update_openapi_spec(spec_path)

        print('✅ Successfully updated OpenAPI specification!')
        print(f'   OpenAPI version: {new_spec.get("openapi", "N/A")}')
        print(f'   API version: {new_spec.get("info", {}).get("version", "N/A")}')
        print(f'   Total endpoints: {len(new_spec.get("paths", {}))}')
        print(f'   Servers: {len(new_spec.get("servers", []))}')

        # List some key endpoints
        paths = list(new_spec.get('paths', {}).keys())
        if paths:
            print('   Sample endpoints:')
            for path in sorted(paths)[:5]:
                methods = list(new_spec['paths'][path].keys())
                print(f'     {path}: {methods}')
            if len(paths) > 5:
                print(f'     ... and {len(paths) - 5} more')

    except Exception as e:
        print(f'❌ Error updating OpenAPI specification: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
