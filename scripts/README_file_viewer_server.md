# OpenHands File Viewer Server

This is a tiny, isolated server that provides only the `/view` endpoint from the action execution server. It has no authentication and only listens to localhost traffic.

## Features

- Serves the `/view` endpoint for viewing files
- Supports various file types including:
  - PDF files
  - Image files (PNG, JPG, JPEG, GIF)
- Runs on localhost only for security
- Saves the server URL to `/tmp/oh-server-url`
- Automatically starts when the action execution server starts
- Dynamically finds an available port

## Usage

The file viewer server starts automatically when the action execution server starts. You don't need to start it manually.

### Viewing Files

Once the server is running, you can view files by accessing the `/view` endpoint with the `path` parameter:

```
http://localhost:8000/view?path=/absolute/path/to/your/file
```

### Using with Browser Tool

The server URL is saved to `/tmp/oh-server-url`, which can be used by the browser tool to view files:

```python
# Example code for browser tool
import os

with open('/tmp/oh-server-url', 'r') as f:
    server_url = f.read().strip()

# View a file
file_path = '/path/to/your/file.pdf'
browser.goto(f"{server_url}/view?path={file_path}")
```

## Security Considerations

- The server only listens on localhost (127.0.0.1) for security reasons
- There is no authentication, so any process on the local machine can access the server
- The server validates that file paths are absolute and exist before serving them