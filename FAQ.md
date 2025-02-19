# OpenHands FAQ

## Table of Contents
- [Docker Memory Management](#docker-memory-management)
  - [Handling Out-of-Memory (OOM) Errors](#handling-out-of-memory-oom-errors)
  - [Configuring Docker Memory Limits](#configuring-docker-memory-limits)
  - [Best Practices](#best-practices)

## Docker Memory Management

### Handling Out-of-Memory (OOM) Errors

#### Q: Why am I getting out-of-memory errors in my Docker container despite having sufficient host memory?

A: This typically occurs when Docker containers don't have explicit memory limits set, or when the limits are set too low. By default, a container can use as much memory as the host's kernel scheduler allows. When running in Docker Desktop, containers are running inside a VM which has its own memory limits that may be lower than your host system's total memory.

#### Q: How can I fix OOM errors in Docker Desktop?

1. **Check Current Memory Settings**:
   - Open Docker Desktop
   - Go to Settings (gear icon)
   - Navigate to "Resources"
   - Check the "Memory" allocation

2. **Increase Memory Limits**:
   - Adjust the memory slider to allocate more memory to Docker
   - Recommended: Start with at least 4GB for development workloads
   - Click "Apply & Restart" to apply changes

3. **Alternative Method (using docker-compose.yml)**:
   ```yaml
   services:
     your_service:
       mem_limit: 2g        # Hard memory limit
       memswap_limit: 4g    # Total memory + swap limit
   ```

### Configuring Docker Memory Limits

#### Q: What memory-related settings can I configure?

Docker provides several options to control container memory usage:

1. **Memory Limit** (`--memory` or `-m`):
   ```bash
   docker run -m 2g your_image    # Limits container to 2GB memory
   ```

2. **Memory + Swap** (`--memory-swap`):
   ```bash
   docker run -m 2g --memory-swap 4g your_image    # 2GB memory + 2GB swap
   ```

3. **Memory Reservation** (`--memory-reservation`):
   ```bash
   docker run --memory-reservation 1g your_image    # Soft limit of 1GB
   ```

### Best Practices

1. **Always Set Memory Limits**:
   - Explicitly set memory limits for production containers
   - Monitor memory usage to set appropriate limits
   - Consider both memory and swap limits

2. **Performance Considerations**:
   - Don't set memory limits too low to avoid frequent OOM kills
   - Leave some headroom for memory spikes
   - Consider using memory reservation for soft limits

3. **Monitoring**:
   - Use `docker stats` to monitor container memory usage
   - Implement proper logging to catch OOM events
   - Consider using container monitoring solutions

4. **Resource Planning**:
   - Calculate memory requirements during development
   - Test with production-like workloads
   - Account for peak memory usage

For more detailed information about Docker memory management, refer to the [official Docker documentation on resource constraints](https://docs.docker.com/config/containers/resource_constraints/).
