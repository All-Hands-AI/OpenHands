#!/bin/bash
set -eo pipefail

echo "Starting OpenHands Backend..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - executing migrations"

# Run database migrations
for migration in /app/database/migrations/*.sql; do
  echo "Running migration: $migration"
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f $migration
done

echo "Migrations completed"

# Start the application
echo "Starting application..."
exec "$@"
