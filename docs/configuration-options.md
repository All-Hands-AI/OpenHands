---
id: configuration-options
---

# Configuration Options

This guide details all configuration options available for OpenHands, helping you customize its behavior and integrate it with other services. Required options and those with recommended settings are highlighted.

---

## Table of Contents
1. [General Settings](#general-settings)
2. [AWS Configuration](#aws-configuration)
3. [Base Image and Caching](#base-image-and-caching)
4. [File Uploads](#file-uploads)
5. [Language Model (LLM) Settings](#language-model-llm-settings)
6. [Execution and Security](#execution-and-security)
7. [Workspace Configuration](#workspace-configuration)

---

## General Settings
- **AGENT** (Type: `string`, Default: `null`): Defines the agent type used by OpenHands.
  - **Example**: `"AGENT": "default"`
  
- **AGENT_MEMORY_ENABLED** (Type: `boolean`, Default: `false`): Enables memory persistence for the agent.
  - **Use Case**: Enable to maintain agent state between sessions.
  
- **AGENT_MEMORY_MAX_THREADS** (Type: `integer`, Default: `4`): Maximum threads allocated for agent memory operations.
  - **Example**: Set to `8` for high-memory environments.

## AWS Configuration
- **AWS_ACCESS_KEY_ID** (Type: `string`, Required): Access key for AWS services.
  - **Example**: `"AWS_ACCESS_KEY_ID": "your_aws_key"`
  
- **AWS_REGION_NAME** (Type: `string`, Default: `"us-west-1"`): AWS region for deployment.
  - **Example**: `"AWS_REGION_NAME": "us-east-1"`
  
- **AWS_SECRET_ACCESS_KEY** (Type: `string`, Required): Secret key for AWS API access.

## Base Image and Caching
- **BASE_CONTAINER_IMAGE** (Type: `string`, Default: `"openhands/base:latest"`): Base image for containerized setups.
- **CACHE_DIR** (Type: `string`, Default: `"/tmp/openhands/cache"`): Directory for caching data.
- **CONFIRMATION_MODE** (Type: `boolean`, Default: `true`): Enables confirmation prompts for critical actions.

## File Uploads
- **FILE_UPLOADS_ALLOWED_EXTENSIONS** (Type: `array`, Default: `["pdf", "jpg", "png"]`): Permitted file extensions for uploads.
- **FILE_UPLOADS_MAX_FILE_SIZE_MB** (Type: `integer`, Default: `10`): Maximum file size for uploads (MB).
- **FILE_UPLOADS_RESTRICT_FILE_TYPES** (Type: `boolean`, Default: `true`): Restricts file types to those allowed in `FILE_UPLOADS_ALLOWED_EXTENSIONS`.

## Language Model (LLM) Settings
These settings configure language model integration.

- **LLM_API_KEY** (Type: `string`, Required): API key to access the LLM service.
  - **Example**: `"LLM_API_KEY": "api_key_123"`
  
- **LLM_API_VERSION** (Type: `string`, Default: `"v1"`): Version of the LLM API.
- **LLM_BASE_URL** (Type: `string`, Default: `"https://api.llmprovider.com"`): Base URL for the LLM service.
- **LLM_CACHING_PROMPT** (Type: `boolean`, Default: `false`): Caches prompts for faster processing.
- **LLM_CUSTOM_LLM_PROVIDER** (Type: `string`, Default: `null`): Allows setting a custom provider.
  - **Example**: `"LLM_CUSTOM_LLM_PROVIDER": "myLLMProvider"`
  
- **LLM_DROP_PARAMS** (Type: `array`, Default: `[]`): Parameters to exclude from LLM requests.
  - **Example**: `"LLM_DROP_PARAMS": ["param1", "param2"]`
  
- **LLM_EMBEDDING_BASE_URL** (Type: `string`, Default: `null`): URL for LLM embedding service.
- **LLM_EMBEDDING_DEPLOYMENT_NAME** (Type: `string`, Default: `null`): Name for embedding deployment.
- **LLM_EMBEDDING_MODEL** (Type: `string`, Default: `"default_embedding_model"`): Embedding model used.
- **LLM_MAX_INPUT_TOKENS** (Type: `integer`, Default: `2048`): Maximum tokens for input.
- **LLM_MAX_OUTPUT_TOKENS** (Type: `integer`, Default: `512`): Maximum tokens for output.
- **LLM_MODEL** (Type: `string`, Default: `"default"`): Model type for language processing.
- **LLM_NUM_RETRIES** (Type: `integer`, Default: `3`): Retry attempts for request failures.
- **LLM_RETRY_MAX_WAIT** (Type: `integer`, Default: `60`): Maximum wait time between retries (seconds).
- **LLM_RETRY_MIN_WAIT** (Type: `integer`, Default: `1`): Minimum wait time between retries (seconds).
- **LLM_TEMPERATURE** (Type: `float`, Default: `0.7`): Controls response creativity (range 0-1).
  - **Recommended Setting**: Use `0.5` for factual responses, `0.9` for creative tasks.
  
- **LLM_TIMEOUT** (Type: `integer`, Default: `30`): Timeout for LLM requests (seconds).
- **LLM_TOP_P** (Type: `float`, Default: `0.9`): Controls diversity in output.
- **LLM_DISABLE_VISION** (Type: `boolean`, Default: `false`): Disables vision processing if supported.

## Execution and Security
- **MAX_ITERATIONS** (Type: `integer`, Default: `10`): Maximum iterations per operation.
  - **Example**: Increase to handle larger processes.
  
- **RUN_AS_OPENHANDS** (Type: `boolean`, Default: `false`): Runs the instance as OpenHands.
- **SANDBOX_TIMEOUT** (Type: `integer`, Default: `300`): Timeout for sandboxed environments (seconds).
- **SANDBOX_USER_ID** (Type: `string`, Default: `null`): User ID for sandbox environments.
- **SECURITY_ANALYZER** (Type: `boolean`, Default: `true`): Enables security analysis tools.
- **USE_HOST_NETWORK** (Type: `boolean`, Default: `false`): Enables use of the host network for container operations.

## Workspace Configuration
- **WORKSPACE_BASE** (Type: `string`, Default: `"/var/workspace"`): Root directory for workspace files.
- **WORKSPACE_MOUNT_PATH** (Type: `string`, Default: `"/mnt/workspace"`): Path where workspace is mounted.
- **WORKSPACE_MOUNT_PATH_IN_SANDBOX** (Type: `string`, Default: `"/sandbox/mnt/workspace"`): Workspace mount path in a sandboxed environment.
- **WORKSPACE_MOUNT_REWRITE** (Type: `boolean`, Default: `false`): Enables mount path rewriting.

---

> **Note**: Adjust configurations carefully, especially for memory, security, and network-related settings to ensure optimal performance and security.


