# OpenHands Storage Module

The storage module provides different storage options for file operations in OpenHands, used for storing events, settings and other metadata. This module implements a common interface (`FileStore`) that allows for interchangeable storage backends.

**Usage:**
```python

store = ...

# Write, read, list, and delete operations
store.write("example.txt", "Hello, world!")
content = store.read("example.txt")
files = store.list("/")
store.delete("example.txt")
```

## Available Storage Options

### 1. Local File Storage (`local`)

Local file storage saves files to the local filesystem.

**Environment Variables:**
- None specific to this storage option
- Files are stored at the path specified by `file_store_path` in the configuration

### 2. In-Memory Storage (`memory`)

In-memory storage keeps files in memory, which is useful for testing or temporary storage.

**Environment Variables:**
- None

### 3. Amazon S3 Storage (`s3`)

S3 storage uses Amazon S3 or compatible services for file storage.

**Environment Variables:**
- The bucket name is specified by `file_store_path` in the configuration with a fallback to the `AWS_S3_BUCKET` enviroment variable.
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_S3_ENDPOINT`: Optional custom endpoint for S3-compatible services (Allows overriding the default)
- `AWS_S3_SECURE`: Whether to use HTTPS (default: "true")

### 4. Google Cloud Storage (`google_cloud`)

Google Cloud Storage uses Google Cloud Storage buckets for file storage.

**Environment Variables:**
- The bucket name is specified by `file_store_path` in the configuration with a fallback to the `GOOGLE_CLOUD_BUCKET_NAME` enviroment variable.
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud credentials JSON file

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
