ARG cuda_version=12.4.0
ARG ubuntu_tag=ubuntu20.04
ARG tag="${cuda_version}-devel-${ubuntu_tag}"
FROM nvidia/cuda:${tag} as build-app
ARG cuda_version
ARG ubuntu_version

LABEL org.opencontainers.image.description="Devin with Nvidia CUDA v${cuda_version} and Miniconda3"
LABEL org.opencontainers.image.author="lehcode <53556648+lehcode@users.noreply.github.com>"

ARG debug
#ARG pip_cache_dir=/root/.cache/pip
ARG apt_cache_dir=/var/cache/apt

ARG nvidia_utils_driver=550

ENV DEBUG="$debug"
ENV DEBIAN_FRONTEND=noninteractive

ADD --checksum=sha256:b978856ec3c826eb495b60e3fffe621f670c101150ebcbdeede4f961f22dc438 https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh /tmp/miniconda.sh

RUN --mount=type=cache,target=${apt_cache_dir},sharing=locked \
    if [ -n "${DEBUG}" ]; then set -eux; fi && \
    apt-get -q update && \
    apt-get install -qy --no-install-recommends \
      tzdata locales cpanminus curl git gnupg gnupg2 gnupg1 wget \
      nvidia-utils-${nvidia_utils_driver} && \
    if [ -z "${DEBUG}" ]; then apt-get -qy upgrade; fi

ARG timezone=Etc/UTC
ARG locale

ENV LANG="$locale"
ENV TZ="$timezone"

COPY docker/locales /etc/locale.gen

RUN if [ -n "$debug" ]; then set -eux; fi && \
    ln -fs "/usr/share/zoneinfo/$timezone" /etc/localtime && \
    echo "$TZ" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata locales && \
    apt-get -q update && \
    apt-get -qy upgrade && \
    rm -f /usr/lib/x86_64-linux-gnu/libcudadebugger.so.1 && \
    rm -f /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1 && \
    rm -f /usr/lib/x86_64-linux-gnu/libcuda.so.1 && \
    if [ -z "$debug" ]; then rm -rf /var/lib/apt/lists/*; fi

COPY docker/devin/app/conda.base.tmpl.yml /tmp/environment.yml

ARG conda_dir
ARG venv_name
ARG app_dir

ENV CONDA_PREFIX=$conda_dir
ENV VENV_NAME="$venv_name"
ENV APP_DIR="$app_dir"


ARG app_dir

WORKDIR "$app_dir"

RUN if [ -n "${DEBUG}" ]; then set -eux; fi && \
    mkdir -p "${CONDA_PREFIX}" && \
    bash /tmp/miniconda.sh -b -u -p ${CONDA_PREFIX} && \
    sed -i "s/<CONDA_DIR>/$(echo "${CONDA_PREFIX}/envs/${VENV_NAME}" | sed -e 's/[\/&]/\\&/g')/g" /tmp/environment.yml && \
    sed -i "s/<VENV_NAME>/${VENV_NAME}/g" /tmp/environment.yml

ENV PATH="/root/.local/bin:${CONDA_PREFIX}/bin:${PATH}"
ARG conda_pkgs_dir=$CONDA_PREFIX/pkgs

WORKDIR $CONDA_PREFIX

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "${DEBUG}" ]; then set -eux; fi && \
    conda config --add channels conda && \
    conda config --prepend channels conda-forge && \
    conda config --set channel_priority disabled && \
    conda install -qy pip && \
    conda init -q bash && \
    conda env create -y -f /tmp/environment.yml -n "${VENV_NAME}" 2>&1 > /dev/null

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "${DEBUG}" ]; then set -eux; fi && \
    conda install -q -y -n "${VENV_NAME}" pip

ARG bin_dir=/usr/local/bin

ENV PYTHONPATH="$app_dir"
ENV BIN_DIR="$bin_dir"

WORKDIR "$app_dir"

# Activate Miniconda environment
RUN eval "$(conda shell.bash activate "${VENV_NAME}")"
# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "od_env", "/bin/bash", "-c"]

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "$debug" ]; then set -eux; fi && \
    conda config --add channels anaconda && \
    conda config --add channels conda-forge && \
    conda config --set channel_priority strict && \
    conda install -y uvicorn chromadb jupyter && \
    conda config --add channels pytorch && \
    conda install -y pytorch::pytorch && \
    conda config --add channels microsoft && \
    conda install -y microsoft::playwright && \
    conda config --set channel_priority disabled

COPY .env .
COPY config.toml.template .
COPY requirements.txt .
COPY pyproject.toml .

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "$debug" ]; then set -eux; fi && \
    pip install -r requirements.txt

ARG litellm_port=11111
ARG jupyter_port=37799
ARG workspace_dir

COPY agenthub agenthub
COPY dev_config dev_config
COPY evaluation evaluation
COPY opendevin opendevin
COPY tests tests

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "$debug" ]; then set -eux; fi && \
    conda env export -n "${VENV_NAME}" > environment.yml

RUN if [ -n "$debug" ]; then set -eux; fi && \
    echo "Conda environments info:" && \
    conda info --envs && \
    echo "PYTHONPATH variable:" $(env | grep PYTHONPATH)

COPY docker/devin/app/run_api.py run_api.py
COPY docker/devin/app/entrypoint.sh /docker-entrypoint.sh
COPY docker/devin/app/configure.py "${APP_DIR}/configure_devin"
COPY docker/env_debug.sh "$bin_dir/env_debug"

CMD ["-m", "mixtral", "-e", "llama2"]
