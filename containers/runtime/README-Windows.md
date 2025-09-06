# OpenHands Windows Runtime

This directory contains the OpenHands Windows container runtime implementation, allowing you to run OpenHands in Windows Docker Runtime mode on Windows environments.

## File Description

- `Dockerfile.windows` - Windows container image definition file
- `build-windows-runtime.ps1` - Build script
- `README-Windows.md` - Chinese documentation file
- `README-Windows-EN.md` - This English documentation file

## Prerequisites

1. **Windows 10/11 Enterprise or Professional** - Windows container supported version (**Home edition not supported** because Docker Desktop doesn't support Windows containers on Home edition)
2. **Docker Desktop** - With Windows container support enabled
3. **PowerShell 7+** - For running build scripts and starting services
4. **.NET Core Runtime** - For PowerShell integration
5. **Python 3.12 or 3.13** - For running OpenHands backend
6. **Node.js and npm** - For building frontend
7. **Poetry** - Python package manager
8. **Git** - For cloning repositories

## Running OpenHands

### 1. Clone and Setup OpenHands

```powershell
# Clone repository with Windows support
git clone https://github.com/All-Hands-AI/OpenHands.git
cd OpenHands

# Switch to Windows support branch (if using branch)
git checkout windows_runtime_docker

# Install Python dependencies
poetry install
```

### 2. Build Frontend

```powershell
# Build frontend files
cd frontend
npm install
npm run build
cd ..
```

### 3. Get Windows Runtime Image

#### Method 1: Using Pre-built Image (Recommended)

```powershell
# Pull pre-built image
docker pull shx815666/openhands-windows-runtime:latest

# Re-tag for local use
docker tag shx815666/openhands-windows-runtime:latest openhands-windows-runtime:latest
```

#### Method 2: Building Windows Runtime Image

##### Using Build Script (Recommended)

```powershell
# Run in OpenHands/containers/runtime/ directory
.\build-windows-runtime.ps1
```

##### Manual Build

```powershell
# Run in OpenHands project root directory
docker build -f containers/runtime/Dockerfile.windows -t openhands-windows-runtime:latest .
```

### 4. Set Environment Variables

```powershell
# Set Windows Docker runtime
$env:RUNTIME = "windows-docker"
$env:SANDBOX_RUNTIME_CONTAINER_IMAGE = "openhands-windows-runtime:latest"
```

### 5. Start OpenHands

```powershell
# Start OpenHands service
poetry run uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000 --reload --reload-exclude "./workspace"
```

### 6. Access Application

Open your browser and navigate to: `http://localhost:3000`

> **Note**: If you encounter a `RuntimeError: Directory './frontend/build' does not exist` error, make sure you have built the frontend following step 2.

## Technical Details

### Port Configuration

Windows runtime uses the following port ranges (compatible with OpenHands DockerRuntime):

- **Execution Server Ports**: 30000-34999
- **VSCode Ports**: 35000-39999  
- **Application Port Range 1**: 40000-44999
- **Application Port Range 2**: 45000-49151

### Environment Variables

Key environment variables:

- `POETRY_VIRTUALENVS_PATH`: Poetry virtual environment path
- `PYTHON_ROOT`: Python installation path
- `WORK_DIR`: Working directory path
- `OH_INTERPRETER_PATH`: Python interpreter path

### Directory Structure

```
C:\openhands\
├── poetry\              # Poetry virtual environment
├── code\                # Application code
├── workspace\           # Workspace
└── logs\                # Log files
```

## Windows Runtime Features

### Differences from Linux Runtime

1. **Base Image**: Uses `mcr.microsoft.com/windows/servercore:ltsc2022`
2. **Package Manager**: Uses Chocolatey instead of apt
3. **Environment Management**: Uses Python + Poetry instead of micromamba
4. **Path Separator**: Uses backslash `\` instead of forward slash `/`
5. **Permission Management**: Uses `icacls` instead of `chmod`
6. **Shell**: Uses PowerShell instead of bash
7. **Runtime Type**: Uses `windows-docker` instead of `docker`

### Windows Runtime Class

OpenHands now includes a dedicated `WindowsDockerRuntime` class that:

- Automatically handles Windows path conversion
- Uses Windows-specific port ranges
- Supports Windows container platform
- Provides Windows-specific environment variables
- Optimizes Windows container startup and configuration

## Troubleshooting

### Windows Container Related Issues

#### Docker Container Startup Failure

If Windows containers fail to start:

**Solutions:**
1. Ensure Docker Desktop has Windows container support enabled
2. Check Windows version supports containers (**must be Enterprise or Professional edition, Home edition not supported**)
3. Ensure sufficient disk space and memory
4. Switch to Windows container mode in Docker Desktop settings

#### Frontend Build Error

If you encounter `Directory './frontend/build' does not exist` error:

**Solutions:**
1. Ensure you're in the project root directory
2. Run frontend build commands:
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

### General Windows Issues

For other common Windows-related issues (such as PowerShell integration, .NET Core errors, etc.), please refer to the official documentation:

**[OpenHands Windows Troubleshooting Guide](https://docs.all-hands.dev/usage/windows-without-wsl#troubleshooting)**

This document provides detailed solutions for the following issues:
- "System.Management.Automation" not found error
- CoreCLR errors
- PowerShell 7 installation and configuration
- .NET Core Runtime installation
- Other Windows compatibility issues

## Development

### Modifying Dockerfile

If you need to modify Windows runtime configuration:

1. Edit `Dockerfile.windows`
2. Rebuild the image
3. Test the changes

### Adding Dependencies

Add new dependencies in the Dockerfile:

```dockerfile
# Add in appropriate location
RUN pwsh -Command "choco install <package-name> -y"
```

### Custom Environment Variables

Add custom environment variables in the Dockerfile:

```dockerfile
ENV CUSTOM_VAR=value
```

### Debugging Containers

Enter running containers for debugging:

```powershell
# View container list
docker ps

# Enter container
docker exec -it <container-name> pwsh

# View container logs
docker logs <container-name>
```

## Differences from Official Documentation

Key differences between this Windows Runtime implementation and the [official Windows documentation](https://docs.all-hands.dev/usage/windows-without-wsl):

1. **Runtime Type**: Uses `windows-docker` instead of `local`
2. **Containerization**: Runs in Windows containers instead of directly on the host
3. **Isolation**: Provides better environment isolation and consistency
4. **Deployment**: Supports image distribution and deployment

## Contributing

Issues and Pull Requests are welcome to improve Windows runtime support.

## License

Same license as the OpenHands project.
