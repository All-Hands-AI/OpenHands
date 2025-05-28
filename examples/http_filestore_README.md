# HTTP FileStore

This directory contains an implementation of the FileStore interface that uses HTTP requests to store and retrieve files. It allows OpenHands to store files on a remote HTTP server that implements a simple REST API.

## HTTPFileStore

The `HTTPFileStore` class is implemented in `/openhands/storage/http.py`. It provides the following features:

- Store and retrieve files using HTTP requests
- Support for API key, basic auth, and bearer token authentication
- Configurable timeout and SSL verification
- Error handling with appropriate exceptions

## API Requirements

The HTTP server must implement the following endpoints:

- `POST /files/{path}` - Write a file
- `GET /files/{path}` - Read a file
- `GET /files/{path}/list` - List files in a directory
- `DELETE /files/{path}` - Delete a file or directory

## Example Server

An example server implementation is provided in `http_filestore_server.py`. It uses Flask to implement the required API endpoints and can be used as a reference for creating a compatible server.

### Running the Example Server

```bash
# Install dependencies
pip install flask flask-cors

# Run the server
python http_filestore_server.py --port 8000 --host 0.0.0.0 --storage-dir /tmp/filestore
```

### Configuration

The example server can be configured using environment variables:

- `STORAGE_DIR` - Directory to store files in (default: `/tmp/filestore`)
- `API_KEY` - API key for authentication
- `USERNAME` - Username for basic authentication
- `PASSWORD` - Password for basic authentication
- `BEARER_TOKEN` - Bearer token for authentication

## Example Usage

An example script demonstrating how to use the `HTTPFileStore` is provided in `http_filestore_example.py`.

### Running the Example

```bash
# Run the example
python http_filestore_example.py --url http://localhost:8000 --api-key my-api-key
```

## Using HTTPFileStore in Your Code

```python
from openhands.storage.http import HTTPFileStore

# Create a store with API key authentication
store = HTTPFileStore(
    base_url="http://example.com/api",
    api_key="my-api-key"
)

# Or with basic authentication
store = HTTPFileStore(
    base_url="http://example.com/api",
    username="user",
    password="pass"
)

# Or with bearer token authentication
store = HTTPFileStore(
    base_url="http://example.com/api",
    bearer_token="my-token"
)

# Write a file
store.write("/path/to/file.txt", "Hello, world!")

# Read a file
content = store.read("/path/to/file.txt")

# List files in a directory
files = store.list("/path/to")

# Delete a file or directory
store.delete("/path/to/file.txt")
```

## Security Considerations

- Use HTTPS for production deployments
- Implement proper authentication and authorization
- Consider rate limiting to prevent abuse
- Validate file paths to prevent directory traversal attacks
- Set appropriate file size limits
