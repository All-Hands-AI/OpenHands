# Changelog

## [0.51.1] - 2025-08-05

### **Dynamic Subpath Configuration Support**

**Added**: Comprehensive support for serving OpenHands under custom subpaths (e.g., `/c3/c3openhands/`) for reverse proxy and multi-tenant deployments.

**Key Features**:
- Dynamic Vite proxy configuration that automatically handles any subpath
- Runtime Docker frontend rebuilds when `OPENHANDS_BASE_PATH` environment variable is set
- Single Docker image works with any subpath without rebuilding
- Backward compatible - existing root path deployments continue working unchanged

**Usage**: Set `VITE_APP_BASE_URL="/your-path/"` for development or `OPENHANDS_BASE_PATH="/your-path/"` for Docker deployments.
