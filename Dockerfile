# Stage 1: Builder stage
FROM python:3.11 AS builder

# Set working directory
WORKDIR /usr/src/app

# Copy application files
COPY . .

# Install build dependencies
#TODO: are these really needed? 
RUN apk update && \
    apk add --no-cache build-base libffi-dev openssl-dev cargo

# Create virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install pipenv
RUN pip install pipenv

# Install project dependencies
# RUN pipenv install --deploy --ignore-pipfile
RUN pipenv install -v

# -----------------------------------------------------------------------------
# Stage 2: Production stage
FROM docker:26.0.0-dind AS production

# Set working directory
WORKDIR /usr/src/app

# Copy application files from the builder stage
COPY --from=builder /venv /venv
COPY --from=builder /usr/src/app .

# Expose port for Uvicorn app
EXPOSE 3000

# Command to run the Uvicorn app
CMD ["/venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]
