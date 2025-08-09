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
- The bucket name is specified by `file_store_path` in the configuration with a fallback to the `AWS_S3_BUCKET` environment variable.
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_S3_ENDPOINT`: Optional custom endpoint for S3-compatible services (Allows overriding the default)
- `AWS_S3_SECURE`: Whether to use HTTPS (default: "true")

### 4. Google Cloud Storage (`google_cloud`)

Google Cloud Storage uses Google Cloud Storage buckets for file storage.

**Environment Variables:**
- The bucket name is specified by `file_store_path` in the configuration with a fallback to the `GOOGLE_CLOUD_BUCKET_NAME` environment variable.
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud credentials JSON file

## Webhook Protocol

The webhook protocol allows for integration with external systems by sending HTTP requests when files are written or deleted.

### Overview

The `WebHookFileStore` wraps another `FileStore` implementation and sends HTTP requests to a specified URL whenever files are written or deleted. This enables real-time notifications and synchronization with external systems.

**Configuration Options:**
- `file_store_web_hook_url`: The base URL for webhook requests
- `file_store_web_hook_headers`: HTTP headers to include in webhook requests
- `file_store_web_hook_batch`: Whether to use batched webhook requests (default: false)

### Protocol Details

#### Standard Webhook Protocol (Non-Batched)

1. **File Write Operation**:
   - When a file is written, a POST request is sent to `{base_url}{path}`
   - The request body contains the file contents
   - The operation is retried up to 3 times with a 1-second delay between attempts

2. **File Delete Operation**:
   - When a file is deleted, a DELETE request is sent to `{base_url}{path}`
   - The operation is retried up to 3 times with a 1-second delay between attempts

#### Batched Webhook Protocol

The `BatchedWebHookFileStore` extends the webhook functionality by batching multiple file operations into a single request, which can significantly improve performance when many files are being modified in a short period of time.

1. **Batch Request**:
   - A single POST request is sent to `{base_url}` with a JSON array in the body
   - Each item in the array contains:
     - `method`: "POST" for write operations, "DELETE" for delete operations
     - `path`: The file path
     - `content`: The file contents (for write operations only)
     - `encoding`: "base64" if binary content was base64-encoded (optional)

2. **Batch Triggering**:
   - Batches are sent when one of the following conditions is met:
     - A configurable timeout period has elapsed (controlled by `WEBHOOK_BATCH_TIMEOUT_SECONDS` environment variable, defaults to 5 seconds)
     - The total size of batched content exceeds a configurable limit (controlled by `WEBHOOK_BATCH_SIZE_LIMIT_BYTES` environment variable, defaults to 1MB)
     - The `flush()` method is explicitly called

3. **Error Handling**:
   - The batch request is retried up to 3 times with a 1-second delay between attempts

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

# Optional batched webhook mode (default: false)
file_store_web_hook_batch = true
```

**Environment Variables for Batched Webhook:**
- `WEBHOOK_BATCH_TIMEOUT_SECONDS`: Time in seconds after which a batch is sent (default: 5)
- `WEBHOOK_BATCH_SIZE_LIMIT_BYTES`: Size limit in bytes after which a batch is sent (default: 1048576 (1MB))
