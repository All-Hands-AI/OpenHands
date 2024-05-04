#!/bin/bash
# check user is root
if [ "$(id -u)" -ne 0 ]; then
  echo "The OpenDevin entrypoint.sh must run as root"
  exit 1
fi

if [ -z "$SANDBOX_USER_ID" ]; then
  echo "SANDBOX_USER_ID is not set"
  exit 1
fi

# change uid of opendevin user to match the host user
# but the group id is not changed, so the user can still access everything under /app
useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash enduser
usermod -aG app enduser
mkdir -p /home/enduser/.cache/ms-playwright/
mv /home/opendevin/.cache/ms-playwright/ /home/enduser/.cache/

# get the user group of /var/run/docker.sock and set opendevin to that group
DOCKER_SOCKET_GID=$(stat -c '%g' /var/run/docker.sock)
echo "Docker socket group id: $DOCKER_SOCKET_GID"
usermod -aG $DOCKER_SOCKET_GID enduser

# switch to the user and start the server
su enduser -c "cd /app && uvicorn opendevin.server.listen:app --host 0.0.0.0 --port 3000"
