#!/bin/bash
# Extract policy data - do NOT set Content-Type; curl sets it with boundary automatically.
# Usage: ./scripts/curl-extract.sh <path-to-pdf>
# Example: ./scripts/curl-extract.sh policy-docs/test11.pdf

FILE="${1:-policy-docs/test11.pdf}"
OUT="${2:-out_test11.json}"

curl -s -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -F "file=@${FILE}" \
  -o "${OUT}"

echo "Response saved to ${OUT}"
cat "${OUT}" | python3 -m json.tool 2>/dev/null || cat "${OUT}"
