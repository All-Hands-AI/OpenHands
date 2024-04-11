FROM node:21.7.2-bookworm-slim

WORKDIR /OpenDevin

RUN apt-get update -y
RUN apt-get install -y curl make git python3.11 python3-pip
RUN curl -fsSL https://get.docker.com | sh
RUN python3 -m pip install poetry  --break-system-packages

COPY ./frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm install && cd ..

COPY ./frontend/scripts ./frontend/scripts
COPY ./frontend/src/i18n/translation.json ./frontend/src/i18n/translation.json
RUN cd frontend && npm run make-i18n && cd ..

COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install --without evaluation

COPY ./frontend/*.json ./frontend/
COPY ./frontend/*.js ./frontend/
COPY ./frontend/*.ts ./frontend/
COPY ./frontend/src/* ./frontend/src/
COPY ./frontend/public ./frontend/

COPY ./opendevin ./opendevin
COPY ./agenthub ./agenthub
COPY ./entrypoint.sh ./

ENTRYPOINT ["./entrypoint.sh"]
