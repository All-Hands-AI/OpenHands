FROM python:3.11-bookworm

ENV PIPENV_VENV_IN_PROJECT=1
ENV PIP_DEFAULT_TIMEOUT=100


WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock .
RUN pip install poetry && poetry install --only main --no-root --no-directory
COPY . /usr/src/app
RUN poetry install --only main



# RUN python install pipx
# RUN pipx install poetry==1.2.0
# RUN python -m pip install pipenv==2023.12.1 
# RUN python -m pipenv install -v

USER root

VOLUME /usr/src/app/workspace

EXPOSE 3000

CMD ["poetry", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]