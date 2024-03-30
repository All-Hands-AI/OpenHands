FROM python:3.11-slim as build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIPENV_VENV_IN_PROJECT=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc

WORKDIR /app

RUN pip install --upgrade pipenv
RUN pip install --upgrade pip

COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --deploy

# Create user and group "app" and set cache directory for huggingface hub
RUN groupadd -r app && useradd --no-log-init -r -g app app \
    && mkdir -p /app/.cache/huggingface/hub \
    && chown -R app:app /app/.cache/huggingface/hub

USER app

FROM build as runtime

ENV HF_HOME=/app/.cache/huggingface/hub

WORKDIR /app

COPY ./opendevin ./opendevin
COPY ./agenthub ./agenthub

# TODO: migrate to use standard .env file
COPY config.toml .

CMD ["pipenv", "run", "uvicorn", "opendevin.server.listen:app", "--port", "3000", "--reload"]
