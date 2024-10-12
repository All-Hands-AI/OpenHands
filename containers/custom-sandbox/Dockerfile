# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=22

###
# https://hub.docker.com/r/nikolaik/python-nodejs
FROM nikolaik/python-nodejs:python${PYTHON_VERSION}-nodejs${NODE_VERSION} AS base

###
FROM base AS dind
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    sudo

# docker https://docs.docker.com/engine/install/debian/
RUN curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/* && \
	apt-get clean && \
	apt-get autoremove -y

#
RUN usermod -aG docker root
ENV DOCKER_HOST=unix:///var/run/docker.sock

CMD [ "bash" ]
