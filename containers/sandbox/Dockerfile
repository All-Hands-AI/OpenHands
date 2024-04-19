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
    && rm -rf /var/lib/apt/lists/*

RUN service ssh start

RUN pip install jupyterlab notebook jupyter_kernel_gateway
# Add common data science utils
RUN pip install transformers[torch]
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install boilerpy3 pandas datasets sympy scikit-learn matplotlib seaborn
