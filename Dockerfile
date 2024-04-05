FROM python:3.11-bookworm

ENV PIP_REQUESTS_TIMEOUT=100
ENV POETRY_REQUESTS_TIMEOUT=100

WORKDIR /usr/src/app

RUN pip install poetry
RUN poetry --version
RUN python --version

COPY pyproject.toml poetry.lock /usr/src/app/

# https://github.com/OpenDevin/OpenDevin/issues/791
# https://github.com/OpenDevin/OpenDevin/pull/378#issuecomment-2034843314
# https://github.com/pymupdf/PyMuPDF/discussions/1486#discussioncomment-1861977
# https://github.com/pymupdf/PyMuPDF/discussions/875#discussioncomment-554936
RUN poetry run pip install pymupdfb
RUN poetry install --without evaluation
COPY . /usr/src/app

USER root

VOLUME /usr/src/app/workspace

EXPOSE 3000

CMD ["poetry", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]