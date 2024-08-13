FROM ubuntu:22.04

# install basic packages
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    unzip \
    zip \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    openssh-server \
    sudo \
    gcc \
    jq \
    g++ \
    make \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p -m0755 /var/run/sshd

# symlink python3 to python
RUN ln -s /usr/bin/python3 /usr/bin/python

# ==== OpenHands Runtime Client ====
RUN mkdir -p /openhands && mkdir -p /openhands/logs && chmod 777 /openhands/logs
RUN wget --progress=bar:force -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
RUN bash Miniforge3.sh -b -p /openhands/miniforge3
RUN chmod -R g+w /openhands/miniforge3
RUN bash -c ". /openhands/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"
RUN echo "" > /openhands/bash.bashrc
RUN rm -f Miniforge3.sh

# - agentskills dependencies
RUN /openhands/miniforge3/bin/pip install --upgrade pip
RUN /openhands/miniforge3/bin/pip install jupyterlab notebook jupyter_kernel_gateway flake8
RUN /openhands/miniforge3/bin/pip install python-docx PyPDF2 python-pptx pylatexenc openai
RUN /openhands/miniforge3/bin/pip install python-dotenv toml termcolor pydantic python-docx pyyaml docker pexpect tenacity e2b browsergym minio
