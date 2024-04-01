#!/bin/bash

# Ensure the script is run with superuser privileges
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Update package list
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io

# Ensure Docker can be run without sudo
sudo usermod -aG docker $USER
newgrp docker

# Install Python 3.11, NodeJS 14.8, and pipenv
sudo apt-get install -y python3.11 nodejs npm
python3.11 -m pip install --user pipenv

# Pull the latest OpenDevin Docker image
sudo docker pull ghcr.io/opendevin/sandbox

# Copy the config template and set the API key
cp config.toml.template config.toml
echo 'LLM_API_KEY="sk-..."' >> config.toml

# Start the OpenDevin backend
python3.11 -m pipenv install -v
python3.11 -m pipenv shell
uvicorn opendevin.server.listen:app --port 3000 &

# Open a new terminal and navigate to the frontend directory
gnome-terminal -- bash -c 'cd frontend; npm install; npm start; exec bash'

# OpenDevin will be running at localhost:3001
