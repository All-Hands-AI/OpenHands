FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy project files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use virtualenvs
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Copy frontend build
COPY frontend/build/client /app/frontend/build

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/openhands
ENV JWT_SECRET_KEY=changeme
ENV GITHUB_CLIENT_ID=your_github_client_id
ENV GITHUB_CLIENT_SECRET=your_github_client_secret
ENV GOOGLE_CLIENT_ID=your_google_client_id
ENV GOOGLE_CLIENT_SECRET=your_google_client_secret
ENV FRONTEND_URL=https://openhands.fly.dev

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "openhands.server.app_updated"]
