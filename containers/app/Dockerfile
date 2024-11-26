ARG OPENHANDS_BUILD_VERSION=dev

# Frontend builder stage
FROM node:21.7.2-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install -g npm@10.5.1 && npm ci
COPY frontend/ ./
RUN npm run build

# Backend builder stage
FROM python:3.12.3-slim-buster AS backend-builder
WORKDIR /app
COPY ./openhands ./openhands
COPY ./pyproject.toml ./poetry.lock ./

ENV PYTHONPATH='/app' \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update -y && \
    apt-get install -y curl make git build-essential && \
    python3 -m pip install --upgrade poetry==1.8.2 && \
    poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry install --without evaluation,llama-index --no-root && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf $POETRY_CACHE_DIR

# Final stage
FROM python:3.12.3-slim-buster AS openhands-app
WORKDIR /app

ARG OPENHANDS_BUILD_VERSION
ENV RUN_AS_OPENHANDS=true \
    OPENHANDS_USER_ID=42420 \
    SANDBOX_USER_ID=0 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH='/app'

COPY --from=backend-builder /app/openhands ./openhands
COPY --from=backend-builder /app/.venv/lib/python3.12/site-packages /app/.venv/lib/python3.12/site-packages
COPY --from=frontend-builder /app/build ./frontend/build
COPY containers/app/entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE 3000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "openhands.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
