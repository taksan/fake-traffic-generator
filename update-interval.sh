#!/bin/bash

# Script to update log generation interval
# Usage: ./update-interval.sh <min_interval> <max_interval>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <min_interval> <max_interval>"
    echo "Example: $0 0.1 0.5"
    echo ""
    echo "This will set the log generation interval to a random value between min and max seconds"
    exit 1
fi

MIN_INTERVAL=$1
MAX_INTERVAL=$2

echo "Updating log generation interval..."
echo "Min interval: ${MIN_INTERVAL}s"
echo "Max interval: ${MAX_INTERVAL}s"
echo ""

curl -X POST "http://localhost:8000/update_interval" \
  -H "Content-Type: application/json" \
  -d "{\"min_interval\": ${MIN_INTERVAL}, \"max_interval\": ${MAX_INTERVAL}}" \
  | jq '.'

echo ""
