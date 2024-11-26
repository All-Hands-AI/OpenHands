ARG OPENHANDS_BUILD_VERSION=dev

# Frontend builder stage
FROM node:21.7.2-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install -g npm@10.5.1 && npm ci
COPY frontend/ ./
RUN npm run build

# Backend builder stage
FROM python:3.12.3-slim AS backend-builder
WORKDIR /app
COPY openhands/ openhands/
COPY pyproject.toml poetry.lock ./

ENV PYTHONPATH='/app' \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update -y \
    && apt-get install -y curl make git build-essential \
    && python3 -m pip install poetry==1.8.2 \
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --without evaluation,llama-index --no-root

# Final stage
FROM python:3.12.3-slim AS openhands-app
WORKDIR /app

# Environment variables
ARG OPENHANDS_BUILD_VERSION
ENV RUN_AS_OPENHANDS=true \
    OPENHANDS_USER_ID=42420 \
    SANDBOX_LOCAL_RUNTIME_URL=http://host.docker.internal \
    USE_HOST_NETWORK=false \
    WORKSPACE_BASE=/opt/workspace_base \
    OPENHANDS_BUILD_VERSION=$OPENHANDS_BUILD_VERSION \
    SANDBOX_USER_ID=0 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH='/app'

# Create workspace directory
RUN mkdir -p $WORKSPACE_BASE

# Install system dependencies
RUN apt-get update -y \
    && apt-get install -y curl ssh sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure user permissions
RUN groupadd app \
    && useradd -l -m -u $OPENHANDS_USER_ID -s /bin/bash openhands \
    && usermod -aG app openhands \
    && usermod -aG sudo openhands \
    && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN chown -R openhands:app /app && chmod -R 770 /app \
    && chown -R openhands:app $WORKSPACE_BASE && chmod -R 770 $WORKSPACE_BASE

# Copy files from builders
COPY --from=backend-builder /app/openhands ./openhands
COPY --from=backend-builder /app/.venv ./
COPY --from=frontend-builder /app/build ./frontend/build

# Copy configuration files
COPY pyproject.toml poetry.lock README.md MANIFEST.in LICENSE ./
COPY containers/app/entrypoint.sh /app/entrypoint.sh

# Fix permissions
RUN chown -R openhands:app . \
    && chmod -R 770 . \
    && find . -type f -not -perm -220 -exec chmod 664 {} \; \
    && find . -type d -not -perm -770 -exec chmod 770 {} \;

# Set up playwright
RUN playwright install --with-deps chromium

USER root
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "openhands.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
