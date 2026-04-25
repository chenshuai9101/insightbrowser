#!/bin/bash
# InsightBrowser Registry - Start Script

set -e

cd "$(dirname "$0")/.."

echo "🔍 InsightBrowser Registry"
echo "=========================="
echo ""

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Initialize database & seed data
echo "🌱 Seeding demo sites..."
python3 scripts/seed.sh 2>/dev/null || echo "   (Already seeded or will seed on first run)"

echo ""
echo "🚀 Starting server..."
echo "   Home:    http://localhost:7000"
echo "   API:     http://localhost:7000/api"
echo "   Docs:    http://localhost:7000/docs"
echo ""

uvicorn main:app --host 0.0.0.0 --port 7000 --reload
