#!/bin/sh
set -e

echo "=== Running backend tests ==="

if [ ! -d "backend" ]; then
  echo "No backend directory found. Skipping backend tests."
  exit 0
fi

# Run tests only if there are actual test files, otherwise skip gracefully
if ls backend/tests/*test*.py >/dev/null 2>&1 || ls backend/tests/test_*.py >/dev/null 2>&1; then
  cd backend
  if command -v pytest >/dev/null 2>&1; then
    pytest -q
  else
    echo "pytest not found, trying python -m pytest"
    python -m pytest -q
  fi
else
  echo "No backend test files found (backend/tests). Skipping backend tests."
fi


