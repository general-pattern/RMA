#!/bin/bash

echo "🚀 Starting RMA System..."

# Initialize database if it doesn't exist
if [ ! -f "rma.db" ]; then
    echo "📊 Creating database..."
    python init_db.py
    python migrate_db.py
    python migrate_multiple_owners.py
    echo "✅ Database initialized"
else
    echo "✅ Database already exists"
fi

# Start the application
echo "🌐 Starting web server..."
exec gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120