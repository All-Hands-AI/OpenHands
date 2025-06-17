ARG OPENHANDS_BUILD_VERSION=dev
FROM node:22.16.0-bookworm-slim AS frontend-builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.12.10-slim AS base
FROM base AS backend-builder

WORKDIR /app
ENV PYTHONPATH='/app'

ENV UV_CACHE_DIR=/tmp/uv_cache

RUN apt-get update -y \
    && apt-get install -y curl make git build-essential \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv ~/.cargo/bin/uv /usr/local/bin/

COPY pyproject.toml requirements.txt requirements-dev.txt uv.lock ./
RUN touch README.md
RUN uv venv /app/.venv && \
    uv pip install -r requirements.txt && \
    rm -rf $UV_CACHE_DIR

FROM base AS openhands-app

WORKDIR /app

# re-declare for this section
ARG OPENHANDS_BUILD_VERSION

ENV RUN_AS_OPENHANDS=true
# A random number--we need this to be different from the user's UID on the host machine
ENV OPENHANDS_USER_ID=42420
ENV SANDBOX_LOCAL_RUNTIME_URL=http://host.docker.internal
ENV USE_HOST_NETWORK=false
ENV WORKSPACE_BASE=/opt/workspace_base
ENV OPENHANDS_BUILD_VERSION=$OPENHANDS_BUILD_VERSION
ENV SANDBOX_USER_ID=0
ENV FILE_STORE=local
ENV FILE_STORE_PATH=/.openhands
RUN mkdir -p $FILE_STORE_PATH
RUN mkdir -p $WORKSPACE_BASE

RUN apt-get update -y \
    && apt-get install -y curl ssh sudo \
    && rm -rf /var/lib/apt/lists/*

# Default is 1000, but OSX is often 501
RUN sed -i 's/^UID_MIN.*/UID_MIN 499/' /etc/login.defs
# Default is 60000, but we've seen up to 200000
RUN sed -i 's/^UID_MAX.*/UID_MAX 1000000/' /etc/login.defs

RUN groupadd app
RUN useradd -l -m -u $OPENHANDS_USER_ID -s /bin/bash openhands && \
    usermod -aG app openhands && \
    usermod -aG sudo openhands && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN chown -R openhands:app /app && chmod -R 770 /app
RUN sudo chown -R openhands:app $WORKSPACE_BASE && sudo chmod -R 770 $WORKSPACE_BASE
USER openhands

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH='/app'

COPY --chown=openhands:app --chmod=770 --from=backend-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY --chown=openhands:app --chmod=770 ./microagents ./microagents
COPY --chown=openhands:app --chmod=770 ./openhands ./openhands
COPY --chown=openhands:app --chmod=777 ./openhands/runtime/plugins ./openhands/runtime/plugins
COPY --chown=openhands:app pyproject.toml requirements.txt requirements-dev.txt uv.lock README.md MANIFEST.in LICENSE ./

# This is run as "openhands" user, and will create __pycache__ with openhands:openhands ownership
RUN python openhands/core/download.py # No-op to download assets
# Add this line to set group ownership of all files/directories not already in "app" group
# openhands:openhands -> openhands:app
RUN find /app \! -group app -exec chgrp app {} +

COPY --chown=openhands:app --chmod=770 --from=frontend-builder /app/build ./frontend/build
COPY --chown=openhands:app --chmod=770 ./containers/app/entrypoint.sh /app/entrypoint.sh

USER root

WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "openhands.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
