FROM python:3.12.3-slim

WORKDIR /app
ENV PYTHONPATH='/app'
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    AWS_SDK_LOAD_CONFIG=1 \
    SERVE_FRONTEND=false \
    RUN_AS_OPENHANDS=true

# Install system dependencies
RUN apt-get update -y \
    && apt-get install -y \
    build-essential \
    curl \
    git \
    make \
    netcat-openbsd \
    ca-certificates \
    gnupg \
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Install Docker CLI
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker-archive-keyring.gpg \
    && chmod a+r /etc/apt/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock ./

# Install dependencies 
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root \
    && pip install --no-cache-dir boto3>=1.28.0 botocore>=1.31.0 aws-requests-auth awscli docker>=7.0.0

# Set environment variables for runtime
ENV SANDBOX_LOCAL_RUNTIME_URL=http://host.docker.internal
ENV USE_HOST_NETWORK=false
ENV WORKSPACE_BASE=/tmp/workspace
# Use a non-root UID for the sandbox user inside the runtime container to avoid conflicts
# UID 1000 is the conventional first non-root user ID in Linux distributions
ENV SANDBOX_USER_ID=1000
ENV FILE_STORE=local
ENV FILE_STORE_PATH=/.openhands-state

# Create required directories
RUN mkdir -p ${FILE_STORE_PATH} \
    && mkdir -p ${WORKSPACE_BASE} \
    && chmod 777 ${WORKSPACE_BASE}

# Create a docker group with same GID as host (typically 999)
RUN groupadd -g 999 docker || true

# Copy application code (only backend)
COPY openhands/ ./openhands/

# Create a default config.toml
RUN echo '[core]\nworkspace_base="/tmp/workspace"\n\n[llm]\nmodel="bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0"\nbase_url = "https://bedrock-runtime.us-east-1.amazonaws.com"\naws_region_name = "us-east-1"\n\n[sandbox]\nruntime_container_image = "ghcr.io/all-hands-ai/runtime:0.38-nikolaik"\nuse_host_network = false\nruntime_binding_address = "0.0.0.0"\nkeep_runtime_alive = true' > config.toml

# Copy tradejoy specific files
COPY tradejoy/containers/entrypoint.sh /entrypoint.sh

# Make scripts executable
RUN chmod +x /entrypoint.sh

# Create .aws directory
RUN mkdir -p /root/.aws && chmod 700 /root/.aws

# Expose backend port
EXPOSE 3000

# Run the backend server
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "openhands.server.listen:app", "--host", "0.0.0.0", "--port", "3000", "--log-level", "info"] 