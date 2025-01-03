# Custom Sandbox

The sandbox is where the agent performs its tasks. Instead of running commands directly on your computer
(which could be risky), the agent runs them inside a Docker container.

The default OpenHands sandbox (`python-nodejs:python3.12-nodejs22`
from [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) comes with some packages installed such
as python and Node.js but may need other software installed by default.

You have two options for customization:

1. Use an existing image with the required software.
2. Create your own custom Docker image.

## Important Requirements

Before proceeding with either option, note these key requirements:

1. The base image must be Debian-based
2. The user in the container MUST be `root` for proper functionality
3. Any installed packages should be available system-wide, not just for specific users

## Create Your Docker Image

Here's a complete example of a custom runtime Dockerfile:

```dockerfile
FROM debian:latest

# Install required packages
RUN apt-get update && apt-get install -y \
    ruby \
    python3 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Ensure we're running as root
USER root
```

Save this file as `docker/runtime.Dockerfile`. Then, build your Docker image using one of these methods:

### Method 1: Direct Docker Build

```bash
docker build -t local/runtime:latest -f docker/runtime.Dockerfile .
```

### Method 2: Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
services:
  runtime:
    build:
      context: .
      dockerfile: docker/runtime.Dockerfile
    image: local/runtime:latest

  openhands-app:
    image: docker.all-hands.dev/all-hands-ai/openhands:0.14
    environment:
      - SANDBOX_RUNTIME_CONTAINER_IMAGE=local/runtime:latest
      - LOG_ALL_EVENTS=true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - .cache:/home/openhands/.cache
    ports:
      - '3000:3000'
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      - runtime
```

Then run:
```bash
docker-compose up -d
```

## Configuration Options

### Environment Variables

- `SANDBOX_RUNTIME_CONTAINER_IMAGE`: Specifies the custom runtime image (e.g., `local/runtime:latest`)
- `LOG_ALL_EVENTS`: Enable detailed logging (optional)

### Volume Mounts

The following mounts are important:
- `/var/run/docker.sock`: Required for container management
- `.cache:/home/openhands/.cache`: Persistent cache storage

## Common Issues and Troubleshooting

1. **Permission Issues**
   - Ensure the container runs as `root`
   - Verify system-wide package installation
   - Check Docker socket permissions

2. **Image Build Failures**
   - Confirm Debian-based parent image
   - Verify package names and versions
   - Check network connectivity during build

3. **Runtime Errors**
   - Review container logs: `docker logs <container_id>`
   - Verify environment variable settings
   - Check volume mount permissions

## Testing Your Custom Sandbox

1. **Basic Functionality Test**
```bash
# Test basic commands
docker run --rm local/runtime:latest python3 --version
docker run --rm local/runtime:latest node --version
```

2. **Integration Test**
- Start OpenHands with your custom runtime
- Try basic operations (file creation, command execution)
- Verify all required tools are accessible

## Security Considerations

1. **Image Security**
   - Use official base images
   - Keep packages updated
   - Remove unnecessary tools

2. **Runtime Security**
   - Limit exposed ports
   - Use read-only mounts where possible
   - Consider implementing additional container security policies

## Advanced Configuration

For more advanced configurations and detailed technical explanations, refer to:
- [Runtime Documentation](https://docs.all-hands.dev/modules/usage/architecture/runtime#advanced-how-openhands-builds-and-maintains-od-runtime-images)
- [Development Guide](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)
