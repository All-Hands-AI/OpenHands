FROM tiangolo/uvicorn-gunicorn:python3.11-slim

WORKDIR /usr/src/app

COPY . .

RUN python -m pip install --upgrade pipenv

ENV PIP_DEFAULT_TIMEOUT=100
RUN pipenv install --verbose

EXPOSE 3000

CMD pipenv run uvicorn opendevin.server.listen:app --port 3000 --host 0.0.0.0