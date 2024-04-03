FROM docker.io/oz123/pipenv:3.11-v2023-6-26 AS builder

ENV PIPENV_VENV_IN_PROJECT=1

ADD Pipfile.lock Pipfile /usr/src/app/

WORKDIR /usr/src/app

# This is an unfortunate and hacky workaround to mismatched lock files
# https://github.com/pypa/pipenv/issues/1356#issuecomment-1813323742
# RUN /usr/local/bin/pipenv lock --clear 

# RUN /usr/local/bin/pipenv sync
RUN /usr/local/bin/pipenv install --ignore-pipfile

# -----------------------------------------------------------------------------
FROM docker:26.0.0-dind AS runtime

RUN mkdir -v /usr/src/app/.venv

COPY --from=builder /usr/src/app/ /usr/src/app

RUN adduser --uid 1000 devin

WORKDIR /usr/src/app

EXPOSE 3000

USER devin

# Command to run the Uvicorn app
# CMD ["/venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]
CMD ["/usr/src/app/.venv/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]