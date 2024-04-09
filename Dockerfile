# Using base image as the nodejs image from docker hub
FROM node:21.7.2-bookworm-slim

# Creating a working directory in the '/' (root) location
WORKDIR /OpenDevin

# Running shell commands for the container when it is being built
RUN apt-get update -y && \
    apt-get upgrade -y && \

    # Installing required support libraries in the container
    apt-get install curl -y && \
    apt-get install make -y && \
    apt-get install git -y && \
    git config --global safe.directory '*' && \

    # Installing docker in the container
    curl -fsSL https://get.docker.com | sh && \

    # Instaling python3.11, pip and poetry in the container
    apt-get install python3.11 -y && \
    apt-get install python-is-python3 -y && \
    rm /usr/lib/python3.11/EXTERNALLY-MANAGED && \
    apt-get install python3-pip -y && \
    python3 -m pip install poetry && \
    poetry config virtualenvs.create false
