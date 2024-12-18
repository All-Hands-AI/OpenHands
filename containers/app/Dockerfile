ARG OPENHANDS_BUILD_VERSION=dev
FROM --platform=linux/arm64 node:21.7.2-bookworm-slim AS frontend-builder

WORKDIR /app

COPY ./frontend/package.json ./frontend/package-lock.json ./
RUN npm ci

COPY ./frontend ./
RUN npm run build

FROM --platform=linux/arm64 python:3.12.3-slim AS backend-builder

WORKDIR /app
ENV PYTHONPATH='/app'

# Create a virtual environment for Poetry
ENV VENV_PATH=/opt/venv
RUN python3 -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install Poetry in the virtual environment
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl make git build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*

COPY ./pyproject.toml ./poetry.lock ./
RUN touch README.md
RUN poetry install --without evaluation,llama-index --no-root && rm -rf $POETRY_CACHE_DIR

FROM --platform=linux/arm64 python:3.12.3-slim AS openhands-app

WORKDIR /app

ARG OPENHANDS_BUILD_VERSION #re-declare for this section

ENV RUN_AS_OPENHANDS=true
# A random number--we need this to be different from the user's UID on the host machine
ENV OPENHANDS_USER_ID=42420
ENV SANDBOX_LOCAL_RUNTIME_URL=http://host.docker.internal
ENV USE_HOST_NETWORK=false
ENV WORKSPACE_BASE=/opt/workspace_base
ENV OPENHANDS_BUILD_VERSION=$OPENHANDS_BUILD_VERSION
ENV SANDBOX_USER_ID=0
ENV FILE_STORE=local
ENV FILE_STORE_PATH=~/.openhands
RUN mkdir -p $WORKSPACE_BASE

# Install only necessary packages and clean up in the same RUN instruction
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl \
    # ssh \  # Remove if not needed
    # sudo \  # Remove if not needed
    && rm -rf /var/lib/apt/lists/*

# Remove these lines if you remove sudo
# RUN sed -i 's/^UID_MIN.*/UID_MIN 499/' /etc/login.defs
# RUN sed -i 's/^UID_MAX.*/UID_MAX 1000000/' /etc/login.defs

RUN groupadd app
RUN useradd -l -m -u $OPENHANDS_USER_ID -s /bin/bash openhands && usermod -aG app openhands
# Remove these lines if you remove sudo
#    usermod -aG sudo openhands && \
#    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER openhands

# Copy the virtual environment from the backend-builder stage
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH='/app'

COPY --from=backend-builder $VENV_PATH $VIRTUAL_ENV
COPY --from=backend-builder /app/.venv /app/.venv

# Install only necessary Playwright browser(s)
RUN playwright install --with-deps chromium

# Copy only necessary files
COPY ./openhands ./openhands

# This is run as "openhands" user, and will create __pycache__ with openhands:openhands ownership
RUN python openhands/core/download.py # No-op to download assets

COPY --from=frontend-builder /app/build ./frontend/build
COPY ./containers/app/entrypoint.sh /app/entrypoint.sh

USER root
RUN chown -R openhands:app /app
RUN find /app -type d -exec chmod 770 {} \;
RUN find /app -type f -exec chmod 660 {} \;
RUN chmod +x /app/entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "openhands.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]