ARG cuda_version="11.2.2"
ARG ubuntu_tag="ubuntu20.04"
ARG tag="${cuda_version}-base-${ubuntu_tag}"
FROM nvcr.io/nvidia/cuda:${tag} as build-app
ARG cuda_version

LABEL org.opencontainers.image.description="Devin with Nvidia CUDA v${cuda_version} and Miniconda3"
LABEL org.opencontainers.image.author="lehcode <53556648+lehcode@users.noreply.github.com>"

ARG debug
ARG apt_cache_dir="/var/cache/apt"
ARG cuda_driver_branch=535
ARG timezone="Etc/UTC"
ARG lang="C.UTF-8"

ENV DEBUG="${debug}"
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG="${lang}"
ENV TZ="${timezone}"

RUN --mount=type=cache,target="${apt_cache_dir}",sharing=locked \
    if [ -n "${debug}" ]; then set -eux; fi && \
    apt-get -q update > /dev/null && apt-get -y upgrade && \
    apt-get -qy install --no-install-recommends tzdata locales cpanminus curl git wget ca-certificates \
      nvidia-driver-${cuda_driver_branch} nvidia-utils-${cuda_driver_branch}

COPY docker/locales /etc/locale.gen

RUN if [ -n "${debug}" ]; then set -eux; fi && \
    ln -fs "/usr/share/zoneinfo/${timezone}" /etc/localtime > /dev/null && \
    echo "${timezone}" | tee -pa /etc/timezone > /dev/null && \
    dpkg-reconfigure -f noninteractive tzdata locales

ADD --checksum=sha256:3f2e5498e550a6437f15d9cc8020d52742d0ba70976ee8fce4f0daefa3992d2e https://repo.anaconda.com/miniconda/Miniconda3-py311_24.1.2-0-Linux-x86_64.sh /tmp/miniconda.sh

ARG conda_root="/var/miniconda3"
ARG venv_name="od_env"

ENV CONDA_ROOT="${conda_root}"
ENV VENV_NAME="${venv_name}"

RUN if [ -n "${debug}" ]; then set -eux; fi && \
    mkdir -p "${conda_root}" && \
    bash /tmp/miniconda.sh -b -u -p ${conda_root} > /dev/null

ARG conda_pkgs_dir="${CONDA_ROOT}/pkgs"
ARG app_root="/app"
ARG dev_mode

ENV PATH="/root/.local/bin:${conda_root}/bin:${PATH}"
ENV APP_ROOT="${app_root}"
ENV CONDA_NO_PLUGINS=true

WORKDIR "${app_root}"

RUN --mount=type=cache,target="${conda_pkgs_dir}",sharing=locked \
    if [ -n "${debug}" ]; then set -eux; fi && \
    conda config --add channels anaconda  && \
    conda config --add channels microsoft  && \
    conda config --add channels pytorch  && \
    conda config --add channels nvidia  && \
    conda config --add channels conda  && \
    conda config --add channels conda-forge  && \
    conda config --set solver classic && \
    conda install -qy conda=24.4.0 pip && \
    conda create -qy --name "${venv_name}" python=3.12 uvicorn chromadb chroma-hnswlib && \
    conda install -qy --name "${venv_name}" pip && \
    if [ -n "${dev_mode}" ]; then conda install --name ${venv_name} debugpy; fi

COPY pyproject.toml .
COPY poetry.lock .

ENV POETRY_HOME=/etc/poetry
ENV PATH="${POETRY_HOME}/bin:${PATH}"
ENV POETRY_CACHE_DIR=/root/.cache/pypoetry
# If you do not want to install the current project use --no-root.
# If you want to use Poetry only for dependency management but not for packaging,
# you can disable package mode by setting package-mode = false in your pyproject.toml file.
# In a future version of Poetry this warning will become an error!
RUN --mount=type=cache,target=${POETRY_CACHE_DIR} \
    if [ -n "$debug" ]; then set -eux; fi && \
    apt-get install -qy build-essential && \
    conda run -n "${venv_name}" curl -sSL "https://install.python-poetry.org" | python3 - > /dev/null && \
    conda run -n "${venv_name}" poetry --version && \
    conda run -n "${venv_name}" poetry install && \
    conda env export --name "${venv_name}" --file "${app_root}/environment.yml"

COPY agenthub agenthub
COPY dev_config dev_config
COPY evaluation evaluation
COPY opendevin opendevin
COPY tests tests
COPY frontend/dist frontend/dist

COPY docker/env_debug.sh "${app_root}/run/env_debug"
COPY docker/devin/app/entrypoint.sh /docker-entrypoint.sh

ARG dev_mode

ENV DEV_MODE="${dev_mode}"

RUN if [ -n "${debug}" ]; then set -eux; fi && \
    chmod a+x /docker-entrypoint.sh && \
    if [ -z "${dev_mode}" ]; then rm -rf /var/lib/apt/lists/*; fi

ARG devin_api_port

ENV PYTHONPATH="${APP_ROOT}/opendevin"

EXPOSE ${devin_api_port}

# Activate Miniconda environment
RUN eval "$(conda shell.bash activate "${venv_name}")"
# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "${venv_name}", "/bin/bash", "-c"]

ENTRYPOINT ["/docker-entrypoint.sh"]
