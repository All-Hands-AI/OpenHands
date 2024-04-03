FROM python:3.11-bookworm as builder

ENV PIPENV_VENV_IN_PROJECT=1
# ENV PIP_DEFAULT_TIMEOUT=100

ADD . /usr/src/app/

WORKDIR /usr/src/app

RUN pip install pipenv==2023.12.1

# RUN /usr/local/bin/pipenv lock --clear
# RUN /usr/local/bin/pipenv sync -v
RUN /usr/local/bin/pipenv install -v

# -----------------------------------------------------------------------------
FROM docker:26.0.0-dind AS runtime

COPY --from=builder /usr/src/app/ /usr/src/app

WORKDIR /usr/src/app

RUN apk add python
RUN pip install pipenv==2023.12.1

EXPOSE 3000

CMD ["/usr/bin/python", "-m", "pipenv", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]