#!/bin/bash
# Start traffic generation

echo "Starting traffic generation..."
curl -X POST http://localhost:8000/traffic/start \
  -H "Content-Type: application/json" | jq .

echo ""
echo "Traffic generation started!"
