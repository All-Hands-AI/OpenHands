#!/usr/bin/env python3
"""
Example HTTP File Server for HTTPFileStore

This is a simple Flask server that implements the API expected by HTTPFileStore.
It can be used as a reference implementation for creating a compatible server.

API Endpoints:
- POST /files/{path} - Write a file
- GET /files/{path} - Read a file
- GET /files/{path}/list - List files in a directory
- DELETE /files/{path} - Delete a file or directory

Authentication:
- API Key: X-API-Key header
- Basic Auth: HTTP Basic Authentication
- Bearer Token: Authorization header with Bearer scheme

Usage:
    python http_filestore_server.py [--port PORT] [--host HOST] [--storage-dir DIR]

Example:
    python http_filestore_server.py --port 8000 --host 0.0.0.0 --storage-dir /tmp/filestore
"""

import argparse
import json
import os
import shutil
from pathlib import Path

from flask import Flask, Response, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
STORAGE_DIR = os.environ.get('STORAGE_DIR', '/tmp/filestore')
API_KEY = os.environ.get('API_KEY')
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
BEARER_TOKEN = os.environ.get('BEARER_TOKEN')


def authenticate() -> bool:
    """
    Authenticate the request using API key, basic auth, or bearer token.

    Returns:
        bool: True if authentication succeeds, False otherwise
    """
    # If no authentication is configured, allow all requests
    if not any([API_KEY, USERNAME and PASSWORD, BEARER_TOKEN]):
        return True

    # Check API key
    if API_KEY and request.headers.get('X-API-Key') == API_KEY:
        return True

    # Check basic auth
    auth = request.authorization
    if (
        USERNAME
        and PASSWORD
        and auth
        and auth.username == USERNAME
        and auth.password == PASSWORD
    ):
        return True

    # Check bearer token
    auth_header = request.headers.get('Authorization', '')
    if (
        BEARER_TOKEN
        and auth_header.startswith('Bearer ')
        and auth_header[7:] == BEARER_TOKEN
    ):
        return True

    return False


def get_full_path(path: str) -> Path:
    """
    Get the full filesystem path for a given API path.

    Args:
        path: The API path

    Returns:
        Path: The full filesystem path
    """
    # Remove leading slash if present
    if path.startswith('/'):
        path = path[1:]

    return Path(STORAGE_DIR) / path


@app.route('/files/<path:path>', methods=['POST'])
def write_file(path: str) -> Response:
    """
    Write a file.

    Args:
        path: The file path

    Returns:
        Response: HTTP response
    """
    if not authenticate():
        return Response('Unauthorized', status=401)

    full_path = get_full_path(path)

    # Create parent directories if they don't exist
    os.makedirs(full_path.parent, exist_ok=True)

    # Write the file
    with open(full_path, 'wb') as f:
        f.write(request.get_data())

    return Response('', status=201)


@app.route('/files/<path:path>', methods=['GET'])
def read_file(path: str) -> Response:
    """
    Read a file.

    Args:
        path: The file path

    Returns:
        Response: HTTP response with file contents
    """
    if not authenticate():
        return Response('Unauthorized', status=401)

    full_path = get_full_path(path)

    if not full_path.exists():
        return Response(f'File not found: {path}', status=404)

    if not full_path.is_file():
        return Response(f'Not a file: {path}', status=400)

    return send_file(full_path)


@app.route('/files/<path:path>/list', methods=['GET'])
def list_files(path: str) -> Response:
    """
    List files in a directory.

    Args:
        path: The directory path

    Returns:
        Response: HTTP response with JSON list of files
    """
    if not authenticate():
        return Response('Unauthorized', status=401)

    full_path = get_full_path(path)

    if not full_path.exists():
        return Response(f'Directory not found: {path}', status=404)

    if not full_path.is_dir():
        return Response(f'Not a directory: {path}', status=400)

    # Get all files and directories in the directory
    files = []
    for item in full_path.iterdir():
        rel_path = os.path.join(path, item.name)
        if item.is_dir():
            rel_path += '/'
        files.append(rel_path)

    return Response(json.dumps(files), mimetype='application/json')


@app.route('/files/<path:path>', methods=['DELETE'])
def delete_file(path: str) -> Response:
    """
    Delete a file or directory.

    Args:
        path: The file or directory path

    Returns:
        Response: HTTP response
    """
    if not authenticate():
        return Response('Unauthorized', status=401)

    full_path = get_full_path(path)

    if not full_path.exists():
        return Response('', status=204)  # Return success for idempotent deletes

    if full_path.is_file():
        os.remove(full_path)
    elif full_path.is_dir():
        shutil.rmtree(full_path)

    return Response('', status=204)


@app.route('/health', methods=['GET'])
def health_check() -> Response:
    """
    Health check endpoint.

    Returns:
        Response: HTTP response
    """
    return Response(json.dumps({'status': 'ok'}), mimetype='application/json')


def main() -> None:
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description='HTTP File Server for HTTPFileStore')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument(
        '--storage-dir', default=STORAGE_DIR, help='Directory to store files in'
    )

    args = parser.parse_args()

    global STORAGE_DIR
    STORAGE_DIR = args.storage_dir

    # Create storage directory if it doesn't exist
    os.makedirs(STORAGE_DIR, exist_ok=True)

    print(f'Starting HTTP File Server on {args.host}:{args.port}')
    print(f'Storage directory: {STORAGE_DIR}')
    print(
        f'Authentication: {"Enabled" if any([API_KEY, USERNAME and PASSWORD, BEARER_TOKEN]) else "Disabled"}'
    )

    app.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
