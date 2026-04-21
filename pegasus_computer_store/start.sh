#!/bin/bash
# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z postgresdb 5432; do
  sleep 1
done
echo "Database is ready!"

# Run database migrations if needed

# Start the application
exec flask run --host=0.0.0.0 --port=5000
