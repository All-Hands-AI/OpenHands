# OpenHands Dependency Analysis and Reorganization Plan

## Executive Summary

This analysis examines the current dependency structure of OpenHands and provides a detailed plan for reorganizing dependencies into logical groups using Poetry extras. The goal is to enable users to install only the components they need, reducing installation size and complexity.

## Current State Analysis

### Package Structure Overview

OpenHands consists of 15 main packages with the following logical organization:

```
Core Packages (always included):
├── openhands.events (event system - used by 10+ packages)
├── openhands.llm (LLM integration - used by 9+ packages)
├── openhands.runtime (runtime environments - used by 7+ packages)
├── openhands.controller (agent control - used by 4+ packages)
├── openhands.critic (agent evaluation - core functionality)
├── openhands.agenthub (agent implementations)
├── openhands.integrations (third-party services)
├── openhands.storage (data persistence)
├── openhands.security (security features)
├── openhands.memory (memory management)
├── openhands.microagent (microagent system)
├── openhands.mcp (Model Context Protocol)
├── openhands.core (configuration and utilities)
├── openhands.events (event handling)
└── openhands.utils (shared utilities)

Optional Feature Packages:
├── openhands.cli (command-line interface)
├── openhands.resolver (issue resolution)
└── openhands.server (web server and API)
```

### Current Dependency Issues

1. **Monolithic Installation**: All dependencies are currently required, leading to large installations
2. **Unused Dependencies**: Many users install heavy dependencies they never use (e.g., Kubernetes support for local users)
3. **Conflicting Requirements**: Different runtime environments have conflicting or unnecessary cross-dependencies
4. **Development Overhead**: Contributors must install all dependencies even for focused work

### Dependency Categories by Usage Pattern

#### 1. Core Dependencies (Always Required)
These are fundamental to OpenHands operation:

```python
# Core runtime
litellm = "^1.74.3"
aiohttp = ">=3.9.0"
pydantic = "*"
pyyaml = "^6.0.2"
jinja2 = "^3.1.3"
pathspec = "^0.12.1"
python-dotenv = "*"
tenacity = ">=8.5,<10.0"
python-json-logger = "^3.2.1"
prompt-toolkit = "^3.0.50"
python-frontmatter = "^1.1.0"
shellingham = "^1.5.4"
bashlex = "^0.18"
zope-interface = "7.2"
protobuf = "^5.0.0,<6.0.0"
opentelemetry-api = "^1.33.1"
opentelemetry-exporter-otlp-proto-grpc = "^1.33.1"
libtmux = ">=0.37,<0.40"
psutil = "*"
anyio = "4.9.0"
dirhash = "*"
rapidfuzz = "^3.9.0"
whatthepatch = "^1.0.6"
deprecated = "*"
termcolor = "*"
toml = "*"
types-toml = "*"
pyjwt = "^2.9.0"
httpx-aiohttp = "^0.1.8"
```

#### 2. Runtime Dependencies
Used only when running agents in specific environments:

```python
# Docker runtime
docker = "*"  # Only in: runtime/impl/docker/, server/conversation_manager/docker_*

# Kubernetes runtime
kubernetes = "^33.1.0"  # Only in: runtime/impl/kubernetes/

# Browser automation
browsergym-core = "0.13.3"  # Only in: runtime/browser/, agenthub/*browsing*
html2text = "*"  # Used with browsergym

# Process management
pexpect = "*"  # Used in runtime execution

# MCP support
fastmcp = "^2.5.2"  # Only in: mcp/ modules
```

#### 3. Server Dependencies
Used only when running the web server:

```python
# Web framework
fastapi = "*"  # Only in: server/, runtime/action_execution_server.py
uvicorn = "*"  # Server startup
python-multipart = "*"  # File uploads
tornado = "*"  # WebSocket support
python-socketio = "^5.11.4"  # Real-time communication
sse-starlette = "^2.1.3"  # Server-sent events
```

#### 4. Integration Dependencies
Used only for specific third-party integrations:

```python
# Cloud providers
google-generativeai = "*"  # Only in: storage/google_cloud.py
google-api-python-client = "^2.164.0"
google-auth-httplib2 = "*"
google-auth-oauthlib = "*"
google-cloud-aiplatform = "*"
anthropic = { extras = ["vertex"], version = "*" }
boto3 = "*"  # Only in: llm/bedrock.py, storage/s3.py

# Storage backends
redis = ">=5.2,<7.0"  # Not currently used in codebase
minio = "^7.2.8"  # Storage backend

# Payment processing
stripe = ">=11.5,<13.0"  # Payment integration

# Version control
pygithub = "^2.5.0"  # GitHub integration

# Specialized runtimes
openhands-aci = { version = "0.3.1" }  # Azure Container Instances
pythonnet = "*"  # .NET integration
```

#### 5. File Processing Dependencies
Used only for document processing:

```python
# Document formats
PyPDF2 = "*"  # Only in: runtime/plugins/agent_skills/file_reader/
python-pptx = "*"
pylatexenc = "*"
python-docx = "*"
```

#### 6. Development Dependencies
Used only for Jupyter/notebook integration:

```python
# Jupyter ecosystem
ipywidgets = "^8.1.5"  # Not currently used in main codebase
qtconsole = "^5.6.1"  # Not currently used in main codebase
jupyter_kernel_gateway = "*"  # Not currently used in main codebase
```

#### 7. Analysis and Monitoring Dependencies
Used for profiling and analysis:

```python
memory-profiler = "^0.61.0"  # Performance analysis
numpy = "*"  # Data processing
json-repair = "*"  # JSON handling
joblib = "*"  # Parallel processing
```

#### 8. Third-party Runtime Dependencies
Used only for specific runtime environments:

```python
# External runtime providers
e2b = ">=1.0.5,<1.8.0"  # E2B runtime
modal = ">=0.66.26,<1.2.0"  # Modal runtime
runloop-api-client = "0.50.0"  # Runloop runtime
daytona = "0.24.2"  # Daytona runtime
```

## Proposed Extras Structure

### Single Package with Feature-Based Extras

```toml
[tool.poetry.extras]
# Main feature packages
cli = [
    # CLI-specific dependencies (currently minimal)
    # All CLI functionality will be included
]

resolver = [
    # Issue resolution dependencies
    # All resolver functionality will be included
]

server = [
    # Web server dependencies
    "fastapi", "uvicorn", "python-multipart", "tornado",
    "python-socketio", "sse-starlette"
]

# Runtime environment support (part of core but with optional heavy deps)
docker = ["docker"]
kubernetes = ["kubernetes"]
browser = ["browsergym-core", "html2text"]

# File processing capabilities (part of core but with optional deps)
files = ["PyPDF2", "python-pptx", "pylatexenc", "python-docx"]

# Cloud integrations (part of core but with optional deps)
aws = ["boto3", "anthropic"]
google = [
    "google-generativeai", "google-api-python-client",
    "google-auth-httplib2", "google-auth-oauthlib",
    "google-cloud-aiplatform"
]
azure = ["openhands-aci"]

# Storage backends (part of core but with optional deps)
storage = ["redis", "minio"]

# Development tools
dev = ["ipywidgets", "qtconsole", "jupyter_kernel_gateway"]

# Analysis tools
analysis = ["memory-profiler", "numpy", "json-repair", "joblib"]

# External runtimes
e2b = ["e2b"]
modal = ["modal"]
runloop = ["runloop-api-client"]
daytona = ["daytona"]

# Payment processing
payments = ["stripe"]

# Version control integrations
github = ["pygithub"]

# Convenience combinations
local = ["docker", "files"]  # Local development with Docker and file processing
web = ["server", "browser", "files"]  # Web server with browser and file support
cloud = ["aws", "google", "azure", "storage"]  # All cloud integrations
full = ["cli", "resolver", "server", "docker", "kubernetes", "browser", "files",
       "aws", "google", "azure", "storage", "dev", "analysis", "e2b", "modal",
       "runloop", "daytona", "payments", "github"]
```

## Implementation Plan

### Phase 1: Dependency Audit and Cleanup

1. **Remove Unused Dependencies**
   - Audit all dependencies in pyproject.toml against actual usage
   - Remove dependencies that are not imported anywhere
   - Identify dependencies that are only used in tests or evaluation

2. **Identify Dynamic Imports**
   - Search for `importlib.import_module()` calls
   - Find try/except import blocks
   - Document optional dependencies that are imported conditionally

### Phase 2: Code Refactoring

1. **Add Import Guards**
   ```python
   # Example pattern for optional dependencies
   try:
       import docker
   except ImportError:
       docker = None

   def create_docker_runtime():
       if docker is None:
           raise ImportError("Docker support requires 'pip install openhands-ai[runtime]'")
       return DockerRuntime()
   ```

2. **Graceful Degradation**
   - Modify code to handle missing optional dependencies gracefully
   - Provide clear error messages when optional features are used without required dependencies
   - Add runtime checks for optional functionality

3. **Configuration Updates**
   - Update configuration validation to check for required dependencies
   - Add warnings when features are configured but dependencies are missing

### Phase 3: Testing Strategy

1. **Minimal Installation Tests**
   ```bash
   # Test core functionality with minimal dependencies
   pip install openhands-ai
   python -c "import openhands; print('Core import successful')"
   ```

2. **Feature-Specific Tests**
   ```bash
   # Test each extra group
   pip install openhands-ai[runtime]
   pip install openhands-ai[server]
   pip install openhands-ai[browser]
   # etc.
   ```

3. **Integration Tests**
   - Test combinations of extras
   - Verify that missing dependencies are handled gracefully
   - Test upgrade paths from full installation to minimal installation

### Phase 4: Documentation Updates

1. **Installation Guide**
   - Document different installation options
   - Provide use-case specific installation commands
   - Create troubleshooting guide for dependency issues

2. **Migration Guide**
   - Help existing users transition to new installation method
   - Document breaking changes
   - Provide upgrade instructions

## Benefits of This Approach

### For Users

1. **Reduced Installation Size**
   - Core installation: ~50MB instead of ~500MB
   - Users only install what they need
   - Faster installation times

2. **Fewer Conflicts**
   - Reduced chance of dependency conflicts
   - Easier to integrate into existing projects
   - Better compatibility with different Python environments

3. **Clearer Feature Boundaries**
   - Explicit declaration of what features require what dependencies
   - Better understanding of OpenHands architecture
   - Easier to troubleshoot issues

### For Developers

1. **Focused Development**
   - Contributors can install only relevant dependencies
   - Faster development environment setup
   - Clearer separation of concerns

2. **Better Testing**
   - Test different feature combinations
   - Ensure graceful degradation
   - Validate minimal installations

3. **Easier Maintenance**
   - Clear dependency ownership
   - Easier to update specific dependency groups
   - Better understanding of impact of changes

## Implementation Challenges and Solutions

### Challenge 1: Circular Dependencies
**Problem**: Some modules may have circular import dependencies
**Solution**:
- Use lazy imports where possible
- Refactor to break circular dependencies
- Use dependency injection patterns

### Challenge 2: Dynamic Feature Detection
**Problem**: Code needs to detect available features at runtime
**Solution**:
```python
# Feature detection utility
def has_docker_support():
    try:
        import docker
        return True
    except ImportError:
        return False

def require_docker_support():
    if not has_docker_support():
        raise ImportError("Docker support requires 'pip install openhands-ai[runtime]'")
```

### Challenge 3: Configuration Validation
**Problem**: Configuration may reference unavailable features
**Solution**:
- Add runtime validation for configuration options
- Provide clear error messages for missing dependencies
- Allow graceful fallbacks where appropriate

### Challenge 4: Testing Matrix Explosion
**Problem**: Need to test many combinations of extras
**Solution**:
- Focus on common combinations
- Use matrix testing in CI
- Prioritize core + single extra combinations

## Migration Strategy

### For Existing Users

1. **Backward Compatibility**
   - Keep `all` extra that installs everything
   - Default installation remains the same initially
   - Gradual migration over several releases

2. **Communication Plan**
   - Announce changes in release notes
   - Provide migration guide
   - Update documentation with examples

3. **Deprecation Timeline**
   - Release 1: Introduce extras (optional)
   - Release 2: Recommend specific extras
   - Release 3: Change default to minimal installation
   - Release 4: Remove deprecated patterns

### For New Users

1. **Clear Documentation**
   - Installation guide with use-case examples
   - Feature matrix showing what extras enable what functionality
   - Troubleshooting guide for common issues

2. **Helpful Error Messages**
   ```python
   # Example error message
   raise ImportError(
       "Docker runtime requires Docker support. "
       "Install with: pip install openhands-ai[runtime]"
   )
   ```

## Tools for Implementation

### Dependency Analysis Tools

1. **deptry**: Identify unused and missing dependencies
2. **pydeps**: Visualize import graphs
3. **grimp**: Build queryable import graphs for validation
4. **pipreqs**: Generate requirements from actual imports

### Validation Scripts

```python
# Script to validate extras work correctly
def test_extra_group(extra_name, test_imports):
    """Test that an extra group provides required functionality"""
    subprocess.run([sys.executable, "-m", "pip", "install", f"openhands-ai[{extra_name}]"])

    for import_stmt in test_imports:
        try:
            exec(import_stmt)
            print(f"✓ {import_stmt}")
        except ImportError as e:
            print(f"✗ {import_stmt}: {e}")
```

## Conclusion

This reorganization will significantly improve the OpenHands user experience by:

1. **Reducing barrier to entry** with smaller core installation
2. **Improving flexibility** with targeted feature installation
3. **Enhancing maintainability** with clearer dependency boundaries
4. **Enabling better testing** of different configurations

The proposed extras structure balances granularity with usability, providing both fine-grained control and convenient combinations for common use cases.

Implementation should be done gradually with careful attention to backward compatibility and clear communication to users about the benefits and migration path.
