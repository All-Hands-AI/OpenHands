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

# ==== OpenDevin Runtime Client ====
RUN mkdir -p /opendevin && mkdir -p /opendevin/logs && chmod 777 /opendevin/logs
RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opendevin/miniforge3
RUN bash -c ". /opendevin/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"
RUN echo "export PATH=/opendevin/miniforge3/bin:$PATH" >> ~/.bashrc
RUN echo "export PATH=/opendevin/miniforge3/bin:$PATH" >> /opendevin/bash.bashrc

# - agentskills dependencies
RUN /opendevin/miniforge3/bin/pip install --upgrade pip
RUN /opendevin/miniforge3/bin/pip install jupyterlab notebook jupyter_kernel_gateway flake8
RUN /opendevin/miniforge3/bin/pip install python-docx PyPDF2 python-pptx pylatexenc openai opencv-python
