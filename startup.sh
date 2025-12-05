#!/bin/bash

echo "🚀 Starting RMA System..."

# Always initialize database on Render (free tier doesn't persist files)
echo "📊 Initializing database..."
python init_db.py
python migrate_db.py
python migrate_multiple_owners.py
echo "✅ Database initialized"

# Start the application - Use Render's PORT variable
echo "🌐 Starting web server on port ${PORT:-10000}..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120