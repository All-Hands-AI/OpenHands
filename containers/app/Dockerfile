ARG OPENHANDS_BUILD_VERSION=dev

# Frontend builder stage
FROM node:21.7.2-alpine AS frontend-builder
WORKDIR /app

# Copy frontend files
COPY frontend/package*.json ./
RUN npm install -g npm@10.5.1 && npm ci
COPY frontend/ ./
RUN npm run build

# Backend builder stage
FROM python:3.12.3-slim AS backend-builder
WORKDIR /app

# Copy Python files
COPY openhands/ openhands/
COPY pyproject.toml poetry.lock ./

# Setup Python environment
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

[... rest of your Dockerfile ...]
