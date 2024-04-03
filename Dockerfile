FROM docker.io/oz123/pipenv:3.11-2023.07.23 AS builder

ENV PIPENV_VENV_IN_PROJECT=1

ADD Pipfile.lock Pipfile /usr/src/app/

WORKDIR /usr/src/app

RUN /usr/local/bin/pipenv --version
# Upgrade to pipenv-2023.12.1 to fix issue where unable to install dependencies
# https://github.com/pypa/pipenv/issues/1356
RUN pip install pipenv==2023.12.1
RUN /usr/local/bin/pipenv --version

RUN /usr/local/bin/pipenv sync

# -----------------------------------------------------------------------------
FROM docker:26.0.0-dind AS runtime

COPY --from=builder /usr/src/app/ /usr/src/app

RUN adduser --uid 1000 devin

WORKDIR /usr/src/app

EXPOSE 3000

USER devin

CMD ["/usr/src/app/.venv/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]