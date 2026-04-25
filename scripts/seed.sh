#!/bin/bash
# InsightBrowser Registry - Seed Demo Sites
# This script registers the demo agent sites from seeds/ directory

set -e

cd "$(dirname "$0")/.."

echo "🌱 Seeding demo sites into InsightBrowser Registry..."
echo ""

SEED_DIR="seeds"

for seed_file in "$SEED_DIR"/*.json; do
    if [ ! -f "$seed_file" ]; then
        echo "❌ No seed files found in $SEED_DIR/"
        exit 1
    fi

    name=$(python3 -c "import json; print(json.load(open('$seed_file'))['name'])")
    echo "   Registering: $name..."

    python3 -c "
import json, sys
sys.path.insert(0, '.')
from models import init_db, register_site
init_db()
try:
    data = json.load(open('$seed_file'))
    result = register_site(data)
    print(f'   ✅ Registered: {result[\"name\"]} (site_id: {result[\"site_id\"]})')
except Exception as e:
    if 'UNIQUE constraint' in str(e):
        print(f'   ⏭️  Already exists, skipped')
    else:
        print(f'   ❌ Error: {e}')
"
done

echo ""
echo "✅ Seeding complete!"
