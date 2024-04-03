FROM python:3.11-bookworm as builder

ENV PIPENV_VENV_IN_PROJECT=1
ENV PIP_DEFAULT_TIMEOUT=100

ADD . /usr/src/app/

WORKDIR /usr/src/app

# RUN pip install pipenv==2023.12.1

# RUN /usr/local/bin/pipenv lock --clear
# RUN /usr/local/bin/pipenv sync -v
# RUN /usr/local/bin/pipenv install -v

RUN python -m pip install pipenv==2023.12.1
RUN python -m pipenv install -v

EXPOSE 3000

CMD ["python", "-m", "pipenv", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]

# # -----------------------------------------------------------------------------
# # FROM docker:26.0.0-dind AS runtime
# FROM docker:26.0.0-dind

# #COPY --from=builder /usr/src/app/ /usr/src/app
# COPY  . /usr/src/app

# WORKDIR /usr/src/app

# ENV PIPENV_VENV_IN_PROJECT=1
# ENV PYTHON_UNBUFFERED=1

# RUN apk add --no-cache python3 py3-pip
# #TODO: There should be a more intelligent way to install pip
# RUN pip install pipenv==2023.12.1 --break-system-packages --root-user-action=ignore
# RUN python -m pipenv lock --clear
# RUN python -m pipenv install -v --ignore-pipfile

# EXPOSE 3000

# CMD ["/usr/bin/python", "-m", "pipenv", "run", "uvicorn", "opendevin.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]