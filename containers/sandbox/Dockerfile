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
    bash \
    gcc \
    jq \
    g++ \
    make \
    iproute2 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p -m0755 /var/run/sshd

# symlink python3 to python
RUN ln -s /usr/bin/python3 /usr/bin/python

# install basic dependencies for CodeActAgent
RUN pip3 install --upgrade pip
RUN pip3 install jupyterlab notebook jupyter_kernel_gateway flake8
# TODO: those dependencies are needed for agentskills, we should pack them in a new sandbox image
RUN pip3 install python-docx PyPDF2 python-pptx pylatexenc openai opencv-python
