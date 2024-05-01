ARG OPEN_DEVIN_BUILD_VERSION=dev
FROM node:21.7.2-bookworm-slim as frontend-builder

WORKDIR /app

COPY ./frontend/package.json frontend/package-lock.json ./
RUN npm install -g npm@10.5.1
RUN npm ci

COPY ./frontend ./
RUN npm run make-i18n && npm run build

FROM python:3.12-slim as backend-builder

WORKDIR /app
ENV PYTHONPATH '/app'

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update -y \
    && apt-get install -y curl make git build-essential \
    && python3 -m pip install poetry==1.8.2  --break-system-packages

COPY ./pyproject.toml ./poetry.lock ./
RUN touch README.md
RUN poetry install --without evaluation --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.12-slim as runtime

WORKDIR /app

ENV RUN_AS_DEVIN=true
ENV SANDBOX_USER_ID=1000
ENV USE_HOST_NETWORK=false
ENV SSH_HOSTNAME=host.docker.internal
ENV WORKSPACE_BASE=/opt/workspace_base
ENV OPEN_DEVIN_BUILD_VERSION=$OPEN_DEVIN_BUILD_VERSION
RUN mkdir -p $WORKSPACE_BASE

RUN apt-get update -y \
    && apt-get install -y curl ssh sudo

RUN useradd -l -m -u $SANDBOX_USER_ID -s /bin/bash opendevin && \
    usermod -aG sudo opendevin && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN chown -R opendevin:opendevin /app
USER opendevin

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH='/app'

COPY --from=backend-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
# change ownership of the virtual environment to the sandbox user
USER root
RUN chown -R opendevin:opendevin ${VIRTUAL_ENV}
USER opendevin

COPY ./opendevin ./opendevin
COPY ./agenthub ./agenthub
RUN python opendevin/download.py # No-op to download assets
RUN playwright install --with-deps chromium

COPY --from=frontend-builder /app/dist ./frontend/dist

# FIXME: this causes issues with push, and makes the build take forever
#USER root
#RUN chown -R opendevin:opendevin /app
# make group permissions the same as user permissions
#RUN chmod -R g=u /app
#USER opendevin

# change ownership of the app directory to the sandbox user
COPY ./containers/app/entrypoint.sh /app/entrypoint.sh

# run the script as root
USER root
RUN chown opendevin:opendevin /app/entrypoint.sh
RUN chmod 777 /app/entrypoint.sh
CMD ["/app/entrypoint.sh"]
