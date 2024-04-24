FROM node:21.7.2-bookworm-slim as frontend-builder

WORKDIR /app

COPY ./frontend/package.json frontend/package-lock.json ./
RUN npm install -g npm@10.5.1
RUN npm install

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

ENV RUN_AS_DEVIN=false
ENV USE_HOST_NETWORK=false
ENV SSH_HOSTNAME=host.docker.internal
ENV WORKSPACE_BASE=/opt/workspace_base
RUN mkdir -p $WORKSPACE_BASE

RUN apt-get update -y \
    && apt-get install -y curl ssh

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH='/app'

COPY --from=backend-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./opendevin ./opendevin
COPY ./agenthub ./agenthub
RUN python opendevin/download.py # No-op to download assets
RUN playwright install --with-deps chromium

COPY --from=frontend-builder /app/dist ./frontend/dist

CMD ["uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
