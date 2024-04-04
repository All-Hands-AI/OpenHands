FROM nvidia/cuda:12.3.2-devel-ubuntu22.04 as build-sandbox

LABEL org.opencontainers.image.description="Devin server with CUDA support"

ARG venv_dir
ARG debug
ARG conda_dir
ARG ws_dir
ARG node_version

ENV DEBUG=${debug}

RUN --mount=type=cache,target=/var/cache/apt \
    if [ ! -z "${debug}" ]; then set -eux; fi && \
    apt update && apt -qy upgrade

WORKDIR ${venv_dir}

COPY environment.yml .
COPY requirements.txt .

COPY opendevin .

ENV PATH=${PATH}:${conda_dir}/bin

SHELL ["/bin/bash", "-c"]

RUN --mount=type=cache,target=/var/cache/apt \
    if [ ! -z "${debug}" ]; then set -eux; fi && \
    apt update && apt -qy upgrade && \
    apt install -qy --no-install-recommends wget ca-certificates build-essential && \
    mkdir -p /tmp/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -i).sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -u -p ${conda_dir} && \
    sed -i 's|prefix:\s+.+|prefix: '${venv_dir}'|' ./environment.yml && \
    conda env create -f environment.yml

SHELL ["${conda_dir}/bin/conda", "run", "--no-capture-output", "-n", "od", "python3", "-m", "pip", "install", "-r", "/tmp/requirements.txt"]
SHELL ["${conda_dir}/bin/conda", "run", "--no-capture-output", "-n", "od", "python3", "./opendevin/sandbox/sandbox.py", "-d", "${ws_dir}" ]

FROM node:18.20.1-alpine as build-front

ARG venv_dir

WORKDIR ${venv_dir}
COPY frontend .
WORKDIR ${venv_dir}/frontend
#COPY --from=build-sandbox ${venv_dir}/frontend ${venv_dir}/frontend

RUN --mount=type=cache,target=${HOME}/.local/share/pnpm/store \
    apk update && apk add git && \
    set -eux && \
    cd ${venv_dir}/frontend && \
    npm install -g pnpm && \
    pnpm install
#    pnpm run start
