#!/bin/bash
# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z postgresdb 5432; do
  sleep 1
done
echo "Database is ready!"

# Create database tables if they don't exist
echo "Initializing database..."
python3 << 'EOF'
from app import app, db
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
EOF

# Start the application
echo "Starting Flask application..."
gunicorn -w 2 -b 0.0.0.0:5000 app:app