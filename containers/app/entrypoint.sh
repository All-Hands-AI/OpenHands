#!/bin/bash
set -eo pipefail

echo "Starting OpenHands..."
if [[ $NO_SETUP == "true" ]]; then
  echo "Skipping setup, running as $(whoami)"
  "$@"
  exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "The OpenHands entrypoint.sh must run as root"
  exit 1
fi

if [ -z "$SANDBOX_USER_ID" ]; then
  echo "SANDBOX_USER_ID is not set"
  exit 1
fi

if [[ "$SANDBOX_USER_ID" -eq 0 ]]; then
  echo "Running OpenHands as root"
  export RUN_AS_OPENHANDS=false
  mkdir -p /root/.cache/ms-playwright/
  if [ -d "/home/openhands/.cache/ms-playwright/" ]; then
    mv /home/openhands/.cache/ms-playwright/ /root/.cache/
  fi
  "$@"
else
  echo "Setting up enduser with id $SANDBOX_USER_ID"

  if id "enduser" &>/dev/null; then
    echo "User enduser already exists. Skipping creation."
  else
    echo "Creating enduser with ID $SANDBOX_USER_ID"

    if ! useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash enduser; then
      echo "Failed to create user enduser with id $SANDBOX_USER_ID. Incrementing openhands user id."
      incremented_id=$(($SANDBOX_USER_ID + 1))
      usermod -u $incremented_id openhands

      if ! useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash enduser; then
        echo "Failed to create user enduser with id $SANDBOX_USER_ID for a second time. Exiting."
        exit 1
      fi
    fi
  fi

  usermod -aG app enduser

  # Get the user group of /var/run/docker.sock and set enduser to that group
  DOCKER_SOCKET_GID=$(stat -c '%g' /var/run/docker.sock)
  DOCKER_SOCKER_GROUP=$(stat -c '%G' /var/run/docker.sock)
  echo "Docker socket group $DOCKER_SOCKER_GROUP with group ID $DOCKER_SOCKET_GID"

  if getent group $DOCKER_SOCKER_GROUP; then
    echo "Group $DOCKER_SOCKER_GROUP already exists"
  else
    echo "Creating group $DOCKER_SOCKER_GROUP with id $DOCKER_SOCKET_GID"
    groupadd -g $DOCKER_SOCKET_GID docker
  fi

  usermod -aG $DOCKER_SOCKER_GROUP enduser

  mkdir -p /home/enduser/.cache/huggingface/hub/
  mkdir -p /home/enduser/.cache/ms-playwright/
  if [ -d "/home/openhands/.cache/ms-playwright/" ]; then
    mv /home/openhands/.cache/ms-playwright/ /home/enduser/.cache/
  fi

  echo "Running as enduser"
  su enduser /bin/bash -c "${*@Q}" # This magically runs any arguments passed to the script as a command
fi
