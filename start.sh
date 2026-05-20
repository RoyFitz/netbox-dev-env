#!/bin/bash
# Start NetBox development environment

set -e

echo "Starting NetBox development environment..."
docker compose up -d

echo ""
echo "Waiting for NetBox to be ready..."
echo "This may take a minute on first startup..."

# Wait for NetBox to be healthy
until curl -sf http://localhost:8000/login/ > /dev/null 2>&1; do
    sleep 5
    echo "  Still waiting..."
done

echo ""
echo "=========================================="
echo "NetBox is ready!"
echo "=========================================="
echo ""
echo "URL:      http://localhost:8000"
echo "Username: admin"
echo "Password: admin"
echo "API Token: 0123456789abcdef0123456789abcdef01234567"
echo ""
echo "To import data:  ./import.sh"
echo "To view logs:    docker compose logs -f netbox"
echo "To stop:         docker compose down"
echo ""
