FROM node:21.7.2-bookworm-slim as frontend-builder

WORKDIR /app

COPY ./frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY ./frontend ./
RUN npm run build


FROM python:3.12-slim as runtime

WORKDIR /app
ENV PYTHONPATH '/app'

RUN apt-get update -y
RUN apt-get install -y curl make git python3.11 python3-pip
RUN curl -fsSL https://get.docker.com | sh
RUN python3 -m pip install poetry  --break-system-packages

COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install --without evaluation

COPY --from=frontend-builder /app/dist ./frontend/dist

COPY ./opendevin ./opendevin
COPY ./agenthub ./agenthub

ENV RUN_AS_DEVIN=false
ENV USE_HOST_NETWORK=false
ENV SSH_HOSTNAME=host.docker.internal

CMD ["poetry", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
