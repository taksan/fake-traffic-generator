#!/bin/bash
# Stop traffic generation

echo "Stopping traffic generation..."
curl -X POST http://localhost:8000/traffic/stop \
  -H "Content-Type: application/json" | jq .

echo ""
echo "Traffic generation stopped!"
