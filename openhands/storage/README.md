# OpenHands Storage Module

The storage module provides different storage options for file operations in OpenHands. This module implements a common interface (`FileStore`) that allows for interchangeable storage backends.

## Available Storage Options

### 1. Local File Storage (`local`)

Local file storage saves files to the local filesystem.

**Environment Variables:**
- None specific to this storage option
- Files are stored at the path specified by `file_store_path` in the configuration

**Usage:**
```python
from openhands.storage.local import LocalFileStore

# Initialize with a root directory
store = LocalFileStore(root="/path/to/storage")

# Write, read, list, and delete operations
store.write("example.txt", "Hello, world!")
content = store.read("example.txt")
files = store.list("/")
store.delete("example.txt")
```

### 2. In-Memory Storage (`memory`)

In-memory storage keeps files in memory, which is useful for testing or temporary storage.

**Environment Variables:**
- None

**Usage:**
```python
from openhands.storage.memory import InMemoryFileStore

# Initialize with optional initial files
store = InMemoryFileStore()

# Write, read, list, and delete operations
store.write("example.txt", "Hello, world!")
content = store.read("example.txt")
files = store.list("/")
store.delete("example.txt")
```

### 3. Amazon S3 Storage (`s3`)

S3 storage uses Amazon S3 or compatible services for file storage.

**Environment Variables:**
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_S3_BUCKET`: The S3 bucket name (if not provided in constructor)
- `AWS_S3_ENDPOINT`: Optional custom endpoint for S3-compatible services
- `AWS_S3_SECURE`: Whether to use HTTPS (default: "true")

**Usage:**
```python
from openhands.storage.s3 import S3FileStore

# Initialize with a bucket name (or use AWS_S3_BUCKET env var)
store = S3FileStore(bucket_name="my-bucket")

# Write, read, list, and delete operations
store.write("example.txt", "Hello, world!")
content = store.read("example.txt")
files = store.list("/")
store.delete("example.txt")
```

### 4. Google Cloud Storage (`google_cloud`)

Google Cloud Storage uses Google Cloud Storage buckets for file storage.

**Environment Variables:**
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud credentials JSON file
- `GOOGLE_CLOUD_BUCKET_NAME`: The Google Cloud Storage bucket name (if not provided in constructor)

**Usage:**
```python
from openhands.storage.google_cloud import GoogleCloudFileStore

# Initialize with a bucket name (or use GOOGLE_CLOUD_BUCKET_NAME env var)
store = GoogleCloudFileStore(bucket_name="my-bucket")

# Write, read, list, and delete operations
store.write("example.txt", "Hello, world!")
content = store.read("example.txt")
files = store.list("/")
store.delete("example.txt")
```

### 5. Custom Storage Implementation

You can create your own storage implementation by extending the `FileStore` abstract base class.

**Requirements:**
- Implement the `write`, `read`, `list`, and `delete` methods

**Example:**
```python
from openhands.storage.files import FileStore

class MyCustomFileStore(FileStore):
    def write(self, path: str, contents: str | bytes) -> None:
        # Implementation for writing files
        pass

    def read(self, path: str) -> str:
        # Implementation for reading files
        pass

    def list(self, path: str) -> list[str]:
        # Implementation for listing files
        pass

    def delete(self, path: str) -> None:
        # Implementation for deleting files
        pass
```

## Webhook Protocol

The webhook protocol allows for integration with external systems by sending HTTP requests when files are written or deleted.

### Overview

The `WebHookFileStore` wraps another `FileStore` implementation and sends HTTP requests to a specified URL whenever files are written or deleted. This enables real-time notifications and synchronization with external systems.

**Configuration Options:**
- `file_store_web_hook_url`: The base URL for webhook requests
- `file_store_web_hook_headers`: HTTP headers to include in webhook requests

### Protocol Details

1. **File Write Operation**:
   - When a file is written, a POST request is sent to `{base_url}{path}`
   - The request body contains the file contents
   - The operation is retried up to 3 times with a 1-second delay between attempts

2. **File Delete Operation**:
   - When a file is deleted, a DELETE request is sent to `{base_url}{path}`
   - The operation is retried up to 3 times with a 1-second delay between attempts

### Usage Example

```python
import httpx
from openhands.storage.local import LocalFileStore
from openhands.storage.web_hook import WebHookFileStore

# Create the underlying file store
base_store = LocalFileStore(root="/path/to/storage")

# Create a webhook file store that wraps the base store
webhook_store = WebHookFileStore(
    file_store=base_store,
    base_url="https://example.com/api/files",
    client=httpx.Client(headers={"Authorization": "Bearer token"})
)

# Operations on webhook_store will trigger HTTP requests
webhook_store.write("example.txt", "Hello, world!")  # Triggers POST request
webhook_store.delete("example.txt")  # Triggers DELETE request
```

## Configuration

To configure the storage module in OpenHands, use the following configuration options:

```toml
[core]
# File store type: "local", "memory", "s3", "google_cloud"
file_store = "local"

# Path for local file store
file_store_path = "/tmp/file_store"

# Optional webhook URL
file_store_web_hook_url = "https://example.com/api/files"

# Optional webhook headers (JSON string)
file_store_web_hook_headers = '{"Authorization": "Bearer token"}'
```
