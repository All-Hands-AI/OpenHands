FROM ollama/ollama

ARG ws_dir=${ws_dir}

ENV PATH=/miniconda/bin:/miniconda/envs/litellm/bin:${PATH}
ENV LITELLM_PORT=${litellm_port}

RUN --mount=type=cache,target=/var/cache/apt \
    set -eux && \
    apt update && apt -qy upgrade && \
    apt install -y curl && \
    curl -sSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /miniconda.sh && \
    bash /miniconda.sh -b -p /miniconda && \
    rm /miniconda.sh && \
    conda create -y -n litellm_env python=3.11 && \
    conda init

SHELL ["conda", "run", "-n", "litellm_env", "/bin/bash", "-c"]

RUN set -eux && \
    conda clean -afy && \
    pip install litellm[proxy] pymemgpt

COPY litellm_config.yaml .
COPY ./docker/litellm/entrypoint.sh /
