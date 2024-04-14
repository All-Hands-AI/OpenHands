ARG cuda_version=12.4.0
ARG ubuntu_tag=ubuntu20.04
ARG tag="${cuda_version}-devel-${ubuntu_tag}"
FROM nvidia/cuda:${tag} as build-app
ARG cuda_version
ARG ubuntu_version=Ubuntu-20.04

LABEL org.opencontainers.image.description="Devin with Nvidia CUDA v${cuda_version} and Miniconda3"
LABEL org.opencontainers.image.author="lehcode <53556648+lehcode@users.noreply.github.com>"

ARG debug
ARG apt_cache_dir=/var/cache/apt

ARG nvidia_utils_driver=550

ENV DEBUG="$debug"
ENV DEBIAN_FRONTEND=noninteractive

COPY docker/locales /etc/locale.gen

ADD --checksum=sha256:b978856ec3c826eb495b60e3fffe621f670c101150ebcbdeede4f961f22dc438 https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh /tmp/miniconda.sh

RUN --mount=type=cache,target=${apt_cache_dir},sharing=locked \
    if [ -n "${DEBUG}" ]; then set -eux; fi && \
    echo "Updating $ubuntu_version packages..." && \
    apt-get -q update > /dev/null && \
    apt-get install -qy --no-install-recommends \
      tzdata locales cpanminus curl git gnupg gnupg2 gnupg1 wget \
      nvidia-utils-${nvidia_utils_driver} > /dev/null && \
    if [ -z "${DEBUG}" ]; then apt-get -qy upgrade > /dev/null; fi

ARG timezone=Etc/UTC
ARG locale

ENV LANG="$locale"
ENV TZ="$timezone"

RUN --mount=type=cache,target=/usr/share/i18n/locales \
    if [ -n "$debug" ]; then set -eux; fi && \
    echo "Configuring timezone and $ubuntu_version locale..." && \
    ln -fs "/usr/share/zoneinfo/$timezone" /etc/localtime > /dev/null && \
    echo "$TZ" | tee -pa /etc/timezone > /dev/null && \
    dpkg-reconfigure -f noninteractive tzdata locales > /dev/null && \
    apt-get -q update && apt-get -qy upgrade && \
    rm -f /usr/lib/x86_64-linux-gnu/libcudadebugger.so.1 && \
    rm -f /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1 && \
    rm -f /usr/lib/x86_64-linux-gnu/libcuda.so.1 && \
    if [ -z "$debug" ]; then rm -rf /var/lib/apt/lists/*; fi

COPY docker/devin/app/conda.base.tmpl.yml /tmp/environment.yml

ARG conda_root=/var/miniconda3
ARG venv_name
ARG app_root

ENV CONDA_ROOT=$conda_root
ENV VENV_NAME="$venv_name"
ENV APP_ROOT="$app_root"

RUN if [ -n "${DEBUG}" ]; then set -eux; fi && \
    echo "Installing Miniconda..." && \
    mkdir -p "${CONDA_ROOT}" && \
    bash /tmp/miniconda.sh -b -u -p ${CONDA_ROOT} > /dev/null && \
    sed -i "s/<CONDA_DIR>/$(echo "${CONDA_ROOT}/envs/${VENV_NAME}" | sed -e 's/[\/&]/\\&/g')/g" /tmp/environment.yml > /dev/null  && \
    sed -i "s/<VENV_NAME>/${VENV_NAME}/g" /tmp/environment.yml > /dev/null

ENV PATH="/root/.local/bin:${CONDA_ROOT}/bin:${PATH}"
ARG conda_pkgs_dir=$CONDA_ROOT/pkgs

COPY docker/devin/app/.condarc "${CONDA_ROOT}/.condarc"

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "${DEBUG}" ]; then set -eux; fi && \
    conda install -qy pip > /dev/null  && \
    conda init bash > /dev/null  && \
    echo "Configuring ${VENV_NAME} environment..." && \
    conda env create -qy -f /tmp/environment.yml -n "${VENV_NAME}" > /dev/null

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "${DEBUG}" ]; then set -eux; fi && \
    conda install -qy -n "${VENV_NAME}" pip > /dev/null

ARG bin_dir=/usr/local/bin

ENV PYTHONPATH="${APP_ROOT}"
ENV BIN_DIR="$bin_dir"

# Activate Miniconda environment
RUN eval "$(conda shell.bash activate "${VENV_NAME}")"
# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "od_env", "/bin/bash", "-c"]

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "$debug" ]; then set -eux; fi && \
    echo "Setting up Miniconda..." && \
    conda config -q --add channels anaconda > /dev/null && \
    conda config -q --add channels pytorch > /dev/null && \
    conda config -q --add channels microsoft > /dev/null && \
    conda config -q --set channel_priority disabled

WORKDIR "$APP_ROOT"

COPY .env .
COPY pyproject.toml .
COPY README.md .

ENV POETRY_HOME=/etc/poetry
ENV PATH="${POETRY_HOME}/bin:${PATH}"
ENV POETRY_CACHE_DIR=/root/.cache/pypoetry
# If you do not want to install the current project use --no-root.
# If you want to use Poetry only for dependency management but not for packaging, you can disable package mode by
# setting package-mode = false in your pyproject.toml file.
# In a future version of Poetry this warning will become an error!
RUN --mount=type=cache,target=${POETRY_CACHE_DIR} \
    if [ -n "$debug" ]; then set -eux; fi && \
    curl -sSL "https://install.python-poetry.org" | python3 - > /dev/null && poetry --version && \
    echo "Building OpenDevin..." && \
    poetry install --no-root --no-plugins > /dev/null

#ARG litellm_port=11111
#ARG jupyter_port=37799
ARG workspace_dir

COPY agenthub agenthub
COPY dev_config dev_config
COPY evaluation evaluation
COPY opendevin opendevin
COPY tests tests

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "$debug" ]; then set -eux; fi && \
    echo "Installing Jupyter Notebook..." && \
    if [ -n "$debug" ]; then set -eux; fi && \
    conda install -qy jupyter > /dev/null

RUN --mount=type=cache,target=${conda_pkgs_dir},sharing=locked \
    if [ -n "$debug" ]; then set -eux; fi && \
    echo "Dumping ${VENV_NAME} environment config..." && \
    if [ -n "$debug" ]; then set -eux; fi && \
    conda env export -q -n "${VENV_NAME}" -f environment.yml

COPY dev_config/python/.pre-commit-config.yaml /tmp/
COPY .git .git
COPY .gitignore .
COPY .gitattributes .

COPY docker/devin/app/devin_up.py oppendevin_launcher
COPY config.toml.template config.toml
COPY docker/env_debug.sh "${APP_ROOT}/run/env_debug"
COPY docker/devin/app/entrypoint.sh /docker-entrypoint.sh

RUN if [ -n "$debug" ]; then set -eux; fi && \
    echo "Finalizing build..." && \
    git config --unset-all core.hooksPath || true > /dev/null && \
    poetry run pre-commit install --config /tmp/.pre-commit-config.yaml && \
    chmod a+x /docker-entrypoint.sh && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/docker-entrypoint.sh", "-c"]
CMD "-m ${DEFAULT_CHAT_MODEL} -e ${DEFAULT_EMBEDDINGS_MODEL} --"
