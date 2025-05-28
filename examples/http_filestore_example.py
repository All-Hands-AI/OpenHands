#!/usr/bin/env python3
"""
Example usage of HTTPFileStore

This script demonstrates how to use the HTTPFileStore class to interact with
a remote HTTP file server.

Usage:
    python http_filestore_example.py [--url URL] [--api-key API_KEY]

Example:
    python http_filestore_example.py --url http://localhost:8000 --api-key my-api-key
"""

import argparse
import os
import sys
import time

# Add the parent directory to the Python path so we can import the openhands module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openhands.storage.http import HTTPFileStore


def main() -> None:
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description='Example usage of HTTPFileStore')
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the HTTP file server',
    )
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--username', help='Username for basic authentication')
    parser.add_argument('--password', help='Password for basic authentication')
    parser.add_argument('--bearer-token', help='Bearer token for authentication')

    args = parser.parse_args()

    # Create the HTTPFileStore
    store = HTTPFileStore(
        base_url=args.url,
        api_key=args.api_key,
        username=args.username,
        password=args.password,
        bearer_token=args.bearer_token,
    )

    print(f'Connected to HTTP file server at {args.url}')

    # Write a file
    test_file_path = '/test/example.txt'
    test_file_content = f'Hello, world! Created at {time.time()}'
    print(f'Writing file {test_file_path}...')
    store.write(test_file_path, test_file_content)

    # Read the file
    print(f'Reading file {test_file_path}...')
    content = store.read(test_file_path)
    print(f'Content: {content}')

    # Write a file in a subdirectory
    subdir_file_path = '/test/subdir/nested.txt'
    subdir_file_content = 'This is a file in a subdirectory'
    print(f'Writing file {subdir_file_path}...')
    store.write(subdir_file_path, subdir_file_content)

    # List files in the root directory
    print('Listing files in /...')
    files = store.list('/')
    print(f'Files: {files}')

    # List files in the test directory
    print('Listing files in /test...')
    files = store.list('/test')
    print(f'Files: {files}')

    # Delete a file
    print(f'Deleting file {test_file_path}...')
    store.delete(test_file_path)

    # List files again to verify deletion
    print('Listing files in /test after deletion...')
    files = store.list('/test')
    print(f'Files: {files}')

    # Delete a directory
    print('Deleting directory /test...')
    store.delete('/test')

    # List files again to verify deletion
    print('Listing files in / after deletion...')
    files = store.list('/')
    print(f'Files: {files}')

    print('Example completed successfully!')


if __name__ == '__main__':
    main()
