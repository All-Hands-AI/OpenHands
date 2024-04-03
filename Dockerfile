FROM python:3.11-bookworm as builder

ENV PIPENV_VENV_IN_PROJECT=1
ENV PIP_DEFAULT_TIMEOUT=100

ADD . /usr/src/app/

WORKDIR /usr/src/app

RUN python -m pip install pipenv==2023.12.1
RUN python -m pipenv install -v

EXPOSE 3000

CMD ["python", "-m", "pipenv", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]