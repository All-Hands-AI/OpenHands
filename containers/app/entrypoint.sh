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
echo "Creating user opendevin with UID $SANDBOX_USER_ID to run the application"

# add the user to sudoers
useradd -m -u $SANDBOX_USER_ID opendevin && \
usermod -aG sudo opendevin && \
echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# make docker.sock accessible to the user
chmod 777 /var/run/docker.sock

# switch to the user
su - opendevin

# start the application
cd /app
uvicorn opendevin.server.listen:app --host 0.0.0.0 --port 3000
