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

# Create and switch to a new user
RUN useradd --no-create-home appuser
USER appuser

FROM build as runtime

COPY ./opendevin ./opendevin
COPY ./agenthub ./agenthub

# TODO: migrate to use standard .env file
COPY config.toml .

CMD ["pipenv", "run", "uvicorn", "opendevin.server.listen:app", "--port", "3000", "--reload"]
