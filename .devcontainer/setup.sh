#!/bin/bash

# Mark the current repository as safe for Git to prevent "dubious ownership" errors,
# which can occur in containerized environments when directory ownership doesn't match the current user.
git config --global --add safe.directory "$(realpath .)"

# Install `nc`
sudo apt update && sudo apt install netcat -y

# Do common setup tasks
source .openhands/setup.sh
