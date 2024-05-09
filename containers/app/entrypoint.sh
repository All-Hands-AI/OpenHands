#!/bin/bash
# check user is root
echo "Starting OpenDevin..."
if [ "$(id -u)" -ne 0 ]; then
  echo "The OpenDevin entrypoint.sh must run as root"
  exit 1
fi

if [ -z "$SANDBOX_USER_ID" ]; then
  echo "SANDBOX_USER_ID is not set"
  exit 1
fi

if [[ "$SANDBOX_USER_ID" -eq 0 ]]; then
  export RUN_AS_DEVIN=false
  mkdir -p /home/root/.cache/ms-playwright/
  mv /home/opendevin/.cache/ms-playwright/ /home/root/.cache/
else
  echo "Setting up enduser with id $SANDBOX_USER_ID"
  # change uid of opendevin user to match the host user
  # but the group id is not changed, so the user can still access everything under /app
  if ! useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash enduser; then
    echo "Failed to create user enduser with id $SANDBOX_USER_ID. Moving opendevin user."
    incremented_id=$(($SANDBOX_USER_ID + 1))
    usermod -u $incremented_id opendevin
    if ! useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash enduser; then
      echo "Failed to create user enduser with id $SANDBOX_USER_ID for a second time. Exiting."
      exit 1
    fi
  fi
  usermod -aG app enduser
  # get the user group of /var/run/docker.sock and set opendevin to that group
  DOCKER_SOCKET_GID=$(stat -c '%g' /var/run/docker.sock)
  echo "Docker socket group id: $DOCKER_SOCKET_GID"
  usermod -aG $DOCKER_SOCKET_GID enduser
  su enduser
fi

echo "Running as user $(whoami)"
echo "Run as devin: $RUN_AS_DEVIN"
echo "Running command: $@"

"$@" # This runs any command passed to the entrypoint.sh as args, i.e. whatever is in CMD
