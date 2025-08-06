ARG OPENHANDS_BUILD_VERSION=dev
FROM node:24.3.0-bookworm-slim AS frontend-builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.12.10-slim AS base

FROM base AS backend-builder
WORKDIR /app
ENV PYTHONPATH='/app'

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update -y && apt-get install -y curl make git build-essential && python3 -m pip install poetry --break-system-packages

COPY pyproject.toml poetry.lock ./
RUN touch README.md
RUN export POETRY_CACHE_DIR && poetry install --no-root && rm -rf $POETRY_CACHE_DIR

FROM base AS openhands-app
WORKDIR /app

ARG OPENHANDS_BUILD_VERSION
ENV RUN_AS_OPENHANDS=true
ENV OPENHANDS_USER_ID=42420
ENV SANDBOX_LOCAL_RUNTIME_URL=http://host.docker.internal
ENV USE_HOST_NETWORK=false
ENV WORKSPACE_BASE=/opt/workspace_base
ENV OPENHANDS_BUILD_VERSION=$OPENHANDS_BUILD_VERSION
ENV SANDBOX_USER_ID=0
ENV FILE_STORE=local
ENV FILE_STORE_PATH=/.openhands
ENV INIT_GIT_IN_EMPTY_WORKSPACE=1

RUN apt-get update -y && apt-get install -y curl ssh sudo && rm -rf /var/lib/apt/lists/*
RUN sed -i 's/^UID_MIN.*/UID_MIN 499/' /etc/login.defs && sed -i 's/^UID_MAX.*/UID_MAX 1000000/' /etc/login.defs
RUN groupadd app && useradd -l -m -u $OPENHANDS_USER_ID -s /bin/bash openhands && usermod -aG app openhands && usermod -aG sudo openhands && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN mkdir -p $FILE_STORE_PATH $WORKSPACE_BASE && chown -R openhands:app /app && chmod -R 770 /app && chown -R openhands:app $WORKSPACE_BASE && chmod -R 770 $WORKSPACE_BASE

USER openhands

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH='/app'

COPY --chown=openhands:app --chmod=770 --from=backend-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY --chown=openhands:app --chmod=770 ./microagents ./microagents
COPY --chown=openhands:app --chmod=770 ./openhands ./openhands
COPY --chown=openhands:app --chmod=777 ./openhands/runtime/plugins ./openhands/runtime/plugins
COPY --chown=openhands:app pyproject.toml poetry.lock README.md MANIFEST.in LICENSE ./

RUN python openhands/core/download.py
RUN find /app \! -group app -exec chgrp app {} +

COPY --chown=openhands:app --chmod=770 ./containers/app/entrypoint.sh /app/entrypoint.sh
COPY --chown=openhands:app --chmod=770 --from=frontend-builder /app/build ./frontend/build

USER root
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "openhands.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
