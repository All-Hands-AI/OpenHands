FROM litellm/openai-proxy

#ARG ws_dir
ARG venv_dir
ARG apt_proxy
ARG debug

ENV PATH=${PATH}:${venv_dir}/bin
ENV LITELLM_PORT=${litellm_port}
ENV VENV_DIR=${venv_dir}
ENV DEBUG=${debug}

RUN --mount=type=cache,target=/var/cache/apt \
    if [ ! -z "${debug}" ]; then set -eux; fi && \
    apt update && apt -qy upgrade && \
    apt install -y ca-certificates python3 python3-venv python3-pip curl git && \
    python3 -m venv --upgrade-deps ${venv_dir} && \
    python3 -m pip install openai==0.28.1

ENV PATH=${PATH}:/root/.local/bin

RUN if [ ! -z "${debug}" ]; then set -eux; fi && \
    curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /usr/local/src

RUN if [ ! -z "${debug}" ]; then set -eux; fi && \
    git clone https://github.com/cpacker/MemGPT.git ./MemGPT && \
    cd ./MemGPT && \
    . ${venv_dir}/bin/activate && \
    poetry install -E local

COPY ./docker/backends/entrypoint.sh /
