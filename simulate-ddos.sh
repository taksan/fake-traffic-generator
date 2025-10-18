#!/bin/bash

# Script to simulate DDoS attack
# Usage: ./simulate-ddos.sh <duration_seconds> [region]

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <duration_seconds> [region]"
    echo "Example: $0 30"
    echo "Example: $0 60 Asia"
    echo ""
    echo "Available regions:"
    echo "  - Europe"
    echo "  - Asia"
    echo "  - South America"
    echo "  - Africa"
    echo "  - Australia"
    echo "  - North America"
    echo ""
    echo "If no region is specified, a random region will be selected"
    exit 1
fi

DURATION=$1
REGION=${2:-""}

echo "Starting DDoS simulation..."
echo "Duration: ${DURATION} seconds"

if [ -z "$REGION" ]; then
    echo "Region: Random (will be selected automatically)"
    echo ""
    curl -X POST "http://localhost:8000/simulate_ddos" \
      -H "Content-Type: application/json" \
      -d "{\"duration_seconds\": ${DURATION}}" \
      | jq '.'
else
    echo "Region: ${REGION}"
    echo ""
    curl -X POST "http://localhost:8000/simulate_ddos" \
      -H "Content-Type: application/json" \
      -d "{\"duration_seconds\": ${DURATION}, \"region\": \"${REGION}\"}" \
      | jq '.'
fi

echo ""
