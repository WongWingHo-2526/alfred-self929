#!/bin/bash
#!/bin/bash
# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z postgresdb 5432; do
  sleep 1
done
echo "Database is ready!"

# Create database tables
echo "Creating database tables..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Start the application with gunicorn
exec gunicorn --bind 0.0.0.0:5000 app:app
