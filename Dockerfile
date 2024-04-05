FROM python:3.11-bookworm

ENV PIP_REQUESTS_TIMEOUT=100
ENV POETRY_REQUESTS_TIMEOUT=100

WORKDIR /usr/src/app

RUN pip install poetry
RUN poetry --version
RUN python --version
COPY . /usr/src/app

# https://github.com/pymupdf/PyMuPDF/discussions/1486#discussioncomment-1861977
RUN pip install MuPDF

RUN poetry install --without evaluation

#TODO: still getting this missing dependency
# ModuleNotFoundError: No module named 'chromadb'

USER root

VOLUME /usr/src/app/workspace

EXPOSE 3000

CMD ["poetry", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]