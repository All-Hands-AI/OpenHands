OPENDEVIN_WORKSPACE=$(pwd)/workspace
docker run -it \
    --pull=always \
    -e PERSIST_SANDBOX="false" \
    -e WORKSPACE_MOUNT_PATH=$OPENDEVIN_WORKSPACE \
    -e BASE_URL="http://localhost:8000/v1/" \
    -v $OPENDEVIN_WORKSPACE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name opendevin-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/opendevin/opendevin:0.6
