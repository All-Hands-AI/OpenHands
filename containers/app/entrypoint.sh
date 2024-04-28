#!/bin/bash
# check user is root
if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

if [ -z "$SANDBOX_USER_ID" ]; then
  echo "SANDBOX_USER_ID is not set"
  exit 1
fi

# change uid of opendevin user to match the host user
# but the group id is not changed, so the user can still access everything under /app
usermod -u $SANDBOX_USER_ID opendevin

# make docker.sock accessible to the user
chmod 777 /var/run/docker.sock

# switch to the user and start the server
su opendevin -c "cd /app && uvicorn opendevin.server.listen:app --host 0.0.0.0 --port 3000"
