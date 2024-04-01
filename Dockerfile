# Stage 1: Build Python application
FROM python:3.11 AS build

# Set the working directory for the build stage
WORKDIR /usr/src/app

# Copy the Python application source code into the container
COPY --exclude=frontend --exclude=docs --exclude=.github . .

# Install dependencies using Pipenv (assuming Pipfile exists)
RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

# Stage 2: Create DinD container
FROM docker:26.0.0-dind

# Copy Python application from the build stage
COPY --from=build /usr/src/app /usr/src/app

# Set the working directory for the DinD container
WORKDIR /usr/src/app

# Expose port for Uvicorn app
EXPOSE 8000

# Command to run the Uvicorn app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
