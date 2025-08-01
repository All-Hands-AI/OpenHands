FROM python:3.12-slim

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.1.3 \
    RUNTIME=local \
    INSTALL_DOCKER=0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY openhands ./openhands
COPY microagents ./microagents
COPY README.md ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

# Expose port for the webhook server
EXPOSE 8000

# Set environment variables for webhook configuration
ENV GITHUB_WEBHOOK_SECRET=""

# Command to run the server
CMD ["python", "-m", "openhands.server", "--host", "0.0.0.0", "--port", "8000"]