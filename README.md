# OpenHands - Enhanced Fork

This is an enhanced fork of OpenHands with additional features and improved deployment options.

## Quick Start with Docker Compose

The easiest way to run this enhanced version is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/makafeli/OpenHands.git
cd OpenHands

# Start the application
docker-compose up -d
```

The application will be available at http://localhost:3000

## Installation Options

### 1. Docker Compose (Recommended)

This is the easiest way to get started:

```bash
# Clone the repository
git clone https://github.com/makafeli/OpenHands.git
cd OpenHands

# Create .env file (optional)
cp .env.example .env

# Start services
docker-compose up -d
```

### 2. Development Setup

For development with hot-reloading:

```bash
# Start in development mode
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Run tests
docker-compose exec app npm test
```

### 3. Manual Docker Setup

If you prefer the original Docker setup:

```bash
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.19-nikolaik

docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.19-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.19
```

### 4. Local Development

For local development without Docker:

```bash
# Install dependencies
npm install
cd frontend && npm install

# Start development server
npm run dev

# In another terminal, start frontend
cd frontend && npm run dev
```

## Configuration

Create a `.env` file in the root directory:

```env
# Environment
NODE_ENV=development
LOG_ALL_EVENTS=true

# Redis (if using Docker Compose)
REDIS_URL=redis://redis:6379

# Other configurations
API_KEY=your_api_key_here
```

## Enhanced Features

This fork includes several improvements:

1. Docker Compose Integration:
   - Easy deployment
   - Development environment
   - Redis caching
   - Volume persistence

2. Development Features:
   - Hot reloading
   - Development mode
   - Improved error handling
   - Better logging

3. Performance Improvements:
   - Redis caching
   - Optimized builds
   - Better resource management

4. Additional Tools:
   - Health checks
   - Monitoring
   - Easy debugging

## Troubleshooting

### Common Issues

1. Port conflicts:
```bash
# Change the port in docker-compose.yml
ports:
  - "3001:3000"  # Change 3000 to any available port
```

2. Permission issues:
```bash
# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock
```

3. Memory issues:
```bash
# Increase Node.js memory limit
export NODE_OPTIONS=--max_old_space_size=4096
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app

# Check container status
docker-compose ps

# Access container shell
docker-compose exec app sh
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
