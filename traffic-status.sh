#!/bin/bash
# Check traffic generation status

echo "Traffic Generation Status:"
echo "=========================="
curl -s http://localhost:8000/status | jq .

echo ""
echo "API Info:"
echo "========="
curl -s http://localhost:8000/ | jq .
