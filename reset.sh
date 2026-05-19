#!/bin/bash
# Reset the NetBox environment (destroys all data)

set -e

read -p "This will destroy ALL data. Are you sure? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping containers..."
    docker compose down -v

    echo "Environment reset complete."
    echo "Run ./start.sh to start fresh."
else
    echo "Cancelled."
fi
