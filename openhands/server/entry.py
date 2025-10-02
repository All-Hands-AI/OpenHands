"""Server entry point for OpenHands GUI mode."""

import argparse
import os
import sys

import openhands


def main():
    """Main entry point for OpenHands server functionality."""
    # Handle version flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v']:
        print(f'OpenHands version: {openhands.get_version()}')
        sys.exit(0)

    # Create argument parser
    parser = argparse.ArgumentParser(description='OpenHands Server')
    parser.add_argument(
        'command', nargs='?', default='serve', help='Command to run (default: serve)'
    )
    parser.add_argument(
        '--gpu', action='store_true', help='Enable GPU support via nvidia-docker'
    )
    parser.add_argument(
        '--mount-cwd',
        action='store_true',
        help='Mount current working directory into container',
    )
    parser.add_argument(
        '--version', '-v', action='store_true', help='Show version information'
    )

    args = parser.parse_args()

    if args.version:
        print(f'OpenHands version: {openhands.get_version()}')
        sys.exit(0)

    if args.command != 'serve':
        parser.print_help()
        sys.exit(1)

    # Set environment variables based on flags
    if args.gpu:
        os.environ['SANDBOX_RUNTIME_CONTAINER_IMAGE'] = (
            'docker.all-hands.dev/all-hands-ai/runtime:0.58-nikolaik-gpu'
        )

    if args.mount_cwd:
        current_dir = os.getcwd()
        os.environ['SANDBOX_VOLUMES'] = f'{current_dir}:/workspace:rw'

    # Start the server
    from openhands.server.__main__ import main as server_main

    server_main()


if __name__ == '__main__':
    main()
