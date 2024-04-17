FROM ubuntu:22.04

# install basic packages
RUN --mount=type=cache,target=/var/cache/apt \
    apt update && apt -y upgrade \
    && apt install -y  curl wget git vim nano unzip zip python3 python3-pip python3-venv python3-dev \
    build-essential \
    openssh-server \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN service ssh start
