#!/bin/bash
# Import data files from ./data directory into NetBox

set -e

echo "Importing data into NetBox..."
echo ""

docker compose exec -T netbox python /scripts/import_data.py

echo ""
echo "Import complete. View your data at http://localhost:8000"
