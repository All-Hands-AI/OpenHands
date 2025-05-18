#!/bin/bash

# Export AWS credentials
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-your_access_key}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-your_secret_key}" 
export AWS_REGION="${AWS_REGION:-us-east-1}"

# Start the container
docker-compose up -d 