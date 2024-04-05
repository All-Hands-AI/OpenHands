FROM python:3.11-bookworm

ENV PIP_REQUESTS_TIMEOUT=100
ENV POETRY_REQUESTS_TIMEOUT=100

WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock .
RUN pip install poetry && poetry install --only main --no-root --no-directory
COPY . /usr/src/app
RUN poetry install --only main


USER root

VOLUME /usr/src/app/workspace

EXPOSE 3000

CMD ["poetry", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]