#!/bin/bash
set -e

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "Installing flyctl..."
    curl -L https://fly.io/install.sh | sh
    export FLYCTL_INSTALL="/home/ubuntu/.fly"
    export PATH="$FLYCTL_INSTALL/bin:$PATH"
fi

# Login to Fly.io (requires auth token)
if [ -z "$FLY_API_TOKEN" ]; then
    echo "FLY_API_TOKEN environment variable is required"
    exit 1
fi

flyctl auth token "$FLY_API_TOKEN"

# Create Postgres app
echo "Creating Postgres app..."
flyctl apps create openhands-postgres --org personal || true
flyctl volumes create postgres_data --app openhands-postgres --region iad --size 10
flyctl secrets set --app openhands-postgres POSTGRES_PASSWORD="$DB_PASSWORD"
flyctl deploy --app openhands-postgres --config fly/postgres.toml

# Create Redis app
echo "Creating Redis app..."
flyctl apps create openhands-redis --org personal || true
flyctl volumes create redis_data --app openhands-redis --region iad --size 5
flyctl deploy --app openhands-redis --config fly/redis.toml

# Create main app
echo "Creating main app..."
flyctl apps create openhands --org personal || true
flyctl secrets set --app openhands \
    DB_PASSWORD="$DB_PASSWORD" \
    JWT_SECRET="$JWT_SECRET" \
    GITHUB_CLIENT_ID="$GITHUB_CLIENT_ID" \
    GITHUB_CLIENT_SECRET="$GITHUB_CLIENT_SECRET" \
    GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
    GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET"

# Deploy main app
echo "Deploying main app..."
flyctl deploy --app openhands --config fly/fly.toml

echo "Deployment complete!"
echo "Your app is available at: https://openhands.fly.dev"
