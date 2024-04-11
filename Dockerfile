# Using base image as the nodejs image from docker hub
FROM node:21.7.2-bookworm-slim

# Creating a working directory in the '/' (root) location
WORKDIR /OpenDevin

# Running shell commands in the container when it is being built
RUN apt update -y && \

    # Installing required support libraries in the container
    apt install curl make git -y && \
    git config --global safe.directory '*' && \

    # Installing docker in the container
    curl -fsSL https://get.docker.com | sh && \

    # Instaling python3.11, pip and poetry in the container
    apt install python3.11 python-is-python3 python3-pip -y && \
    rm /usr/lib/python3.11/EXTERNALLY-MANAGED && \
    python3 -m pip install poetry && \
    poetry config virtualenvs.create false
