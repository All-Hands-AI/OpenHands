FROM node:21.7.2-bookworm-slim as frontend-builder

WORKDIR /app

COPY ./frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY ./frontend ./
RUN npm run build


FROM python:3.12-slim as runtime

WORKDIR /app
ENV PYTHONPATH '/app'
ENV RUN_AS_DEVIN=false
ENV USE_HOST_NETWORK=false
ENV SSH_HOSTNAME=host.docker.internal
ENV WORKSPACE_BASE=/opt/workspace_base
RUN mkdir -p $WORKSPACE_BASE

RUN apt-get update -y \
    && apt-get install -y curl make git build-essential \
    && python3 -m pip install poetry  --break-system-packages

COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install --without evaluation

COPY ./opendevin ./opendevin
COPY ./agenthub ./agenthub
RUN poetry run python opendevin/download.py # No-op to download assets

COPY --from=frontend-builder /app/dist ./frontend/dist

CMD ["poetry", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
