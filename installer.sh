#!/bin/bash

# Step 1: Build the project
echo "Building the project..."
make build

# Step 2: Setup configuration
echo "Setting up configuration..."
make setup-config

# Step 3: Run the project
echo "Running the project..."
make run &

# Step 4: Start backend server
echo "Starting backend server..."
make start-backend &

# Step 5: Start frontend server
echo "Starting frontend server..."
make start-frontend &

echo "Project installation completed."
