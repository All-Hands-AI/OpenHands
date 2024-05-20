#!/bin/bash
set -eo pipefail

echo "Starting OpenDevin..."
if [[ $NO_SETUP == "true" ]]; then
  echo "Skipping setup, running as $(whoami)"
  "$@"
  exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "The OpenDevin entrypoint.sh must run as root"
  exit 1
fi

if [ -z "$SANDBOX_USER_ID" ]; then
  echo "SANDBOX_USER_ID is not set"
  exit 1
fi

if [[ "$SANDBOX_USER_ID" -eq 0 ]]; then
  echo "Running OpenDevin as root"
  export RUN_AS_DEVIN=false
  mkdir -p /root/.cache/ms-playwright/
  mv /home/opendevin/.cache/ms-playwright/ /root/.cache/
  "$@"
else
  echo "Setting up enduser with id $SANDBOX_USER_ID"
  if id "enduser" &>/dev/null; then
    echo "User enduser already exists. Skipping creation."
  else
    if ! useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash enduser; then
      echo "Failed to create user enduser with id $SANDBOX_USER_ID. Moving opendevin user."
      incremented_id=$(($SANDBOX_USER_ID + 1))
      usermod -u $incremented_id opendevin
      if ! useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash enduser; then
        echo "Failed to create user enduser with id $SANDBOX_USER_ID for a second time. Exiting."
        exit 1
      fi
    fi
  fi
  usermod -aG app enduser
  # get the user group of /var/run/docker.sock and set opendevin to that group
  DOCKER_SOCKET_GID=$(stat -c '%g' /var/run/docker.sock)
  echo "Docker socket group id: $DOCKER_SOCKET_GID"
  if getent group $DOCKER_SOCKET_GID; then
    echo "Group with id $DOCKER_SOCKET_GID already exists"
  else
    echo "Creating group with id $DOCKER_SOCKET_GID"
    groupadd -g $DOCKER_SOCKET_GID docker
  fi

  mkdir -p /home/enduser/.cache/ms-playwright/
  mv /home/opendevin/.cache/ms-playwright/ /home/enduser/.cache/

  usermod -aG $DOCKER_SOCKET_GID enduser
  echo "Running as enduser"
  su enduser /bin/bash -c "$*"
fi
