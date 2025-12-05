#!/bin/bash

echo "🚀 Starting RMA System..."

# Initialize database
echo "📊 Initializing database..."
python init_db.py
python migrate_db.py

# Run the new consolidation migration instead of the old one
if [ -f "migrate_consolidate_users.py" ]; then
    echo "🔄 Running consolidation migration..."
    python migrate_consolidate_users.py
else
    echo "⚠️  Skipping consolidation migration (file not found)"
fi

echo "✅ Database ready"

# Start the application
echo "🌐 Starting web server on port ${PORT:-10000}..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120