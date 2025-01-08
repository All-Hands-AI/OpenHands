#!/bin/bash

# Colors for output
GREEN='[0;32m'
YELLOW='[1;33m'
NC='[0m'

echo -e "${GREEN}Starting OpenHands deployment...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOL
NODE_ENV=development
LOG_ALL_EVENTS=true
EOL
fi

# Build and start containers
echo -e "${GREEN}Building and starting containers...${NC}"
docker-compose up --build -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}OpenHands is now running!${NC}"
    echo -e "Access the application at: ${YELLOW}http://localhost:3000${NC}"
    echo -e "To view logs: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "To stop: ${YELLOW}docker-compose down${NC}"
else
    echo "Error: Services failed to start properly."
    docker-compose logs
    exit 1
fi
