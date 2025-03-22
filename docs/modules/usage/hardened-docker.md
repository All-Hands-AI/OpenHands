# Hardened Docker Installation

When deploying OpenHands in environments where security is a priority, you should consider implementing a hardened Docker configuration. This guide provides recommendations for securing your OpenHands Docker deployment beyond the default configuration.

## Security Considerations

The default Docker configuration in the README is designed for ease of use on a local development machine. For production or multi-user environments, you should implement additional security measures.

### Network Binding Security

By default, OpenHands binds to all network interfaces (`0.0.0.0`), which can expose your instance to all networks the host is connected to. For a more secure setup:

1. **Restrict Network Binding**:
   
   Use the `runtime_binding_address` configuration to restrict which network interfaces OpenHands listens on:

   ```bash
   docker run -it --rm --pull=always \
       -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.29-nikolaik \
       -e LOG_ALL_EVENTS=true \
       -e RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.openhands-state:/.openhands-state \
       -p 127.0.0.1:3000:3000 \
       --add-host host.docker.internal:host-gateway \
       --name openhands-app \
       docker.all-hands.dev/all-hands-ai/openhands:0.29
   ```

   This configuration ensures OpenHands only listens on the loopback interface (`127.0.0.1`), making it accessible only from the local machine.

2. **Secure Port Binding**:

   Modify the `-p` flag to bind only to localhost instead of all interfaces:

   ```bash
   -p 127.0.0.1:3000:3000
   ```

   This ensures that the OpenHands web interface is only accessible from the local machine, not from other machines on the network.

### Docker Socket Security

The Docker socket (`/var/run/docker.sock`) is a powerful interface that gives full control over Docker. When mounting it into a container:

1. **Use a Non-Root User**:

   Create a dedicated user with limited permissions for running OpenHands:

   ```bash
   docker run -it --rm --pull=always \
       -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.29-nikolaik \
       -e LOG_ALL_EVENTS=true \
       -e RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       -e SANDBOX_USER_ID=1000 \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.openhands-state:/.openhands-state \
       -p 127.0.0.1:3000:3000 \
       --add-host host.docker.internal:host-gateway \
       --user 1000:docker \
       --name openhands-app \
       docker.all-hands.dev/all-hands-ai/openhands:0.29
   ```

   Note: This requires that the user with ID 1000 exists in the container and is part of the `docker` group.

2. **Consider Docker Socket Proxies**:

   For enhanced security, consider using a Docker socket proxy like [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) to limit the operations that can be performed on the Docker socket:

   ```bash
   # First, run the socket proxy
   docker run -d --name docker-socket-proxy \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -p 127.0.0.1:2375:2375 \
       -e CONTAINERS=1 \
       tecnativa/docker-socket-proxy

   # Then run OpenHands using the proxy
   docker run -it --rm --pull=always \
       -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.29-nikolaik \
       -e LOG_ALL_EVENTS=true \
       -e RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       -e DOCKER_HOST=tcp://docker-socket-proxy:2375 \
       --link docker-socket-proxy \
       -v ~/.openhands-state:/.openhands-state \
       -p 127.0.0.1:3000:3000 \
       --name openhands-app \
       docker.all-hands.dev/all-hands-ai/openhands:0.29
   ```

### Resource Limitations

Prevent resource exhaustion by setting resource limits:

```bash
docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.29-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -e RUNTIME_BINDING_ADDRESS=127.0.0.1 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 127.0.0.1:3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --cpus=2 \
    --memory=4g \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.29
```

### Network Isolation

Use Docker's network features to isolate OpenHands:

```bash
# Create an isolated network
docker network create openhands-network

# Run OpenHands in the isolated network
docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.29-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -e RUNTIME_BINDING_ADDRESS=127.0.0.1 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 127.0.0.1:3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --network openhands-network \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.29
```

## Complete Hardened Example

Here's a complete example that combines multiple security measures:

```bash
# Create an isolated network
docker network create openhands-network

# Run OpenHands with hardened configuration
docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.29-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -e RUNTIME_BINDING_ADDRESS=127.0.0.1 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 127.0.0.1:3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --cpus=2 \
    --memory=4g \
    --network openhands-network \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.29
```

## Additional Security Recommendations

1. **Keep Docker and OpenHands Updated**: Regularly update to the latest versions to benefit from security patches.

2. **Use Docker Content Trust**: Enable Docker Content Trust to verify image authenticity:
   ```bash
   export DOCKER_CONTENT_TRUST=1
   ```

3. **Implement Network Firewall Rules**: Configure host firewall rules to restrict access to the Docker ports.

4. **Monitor Container Activity**: Use tools like [Falco](https://falco.org/) to monitor for suspicious container activity.

5. **Regular Security Audits**: Periodically review your Docker security configuration and OpenHands deployment.

Remember that security is a balance between usability and protection. Implement the measures that make sense for your specific deployment scenario and security requirements.