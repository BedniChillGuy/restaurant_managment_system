#!/bin/sh
set -e

echo "=== Running frontend tests ==="

if [ -d "frontend" ] && [ -f frontend/package.json ]; then
  cd frontend
  if command -v npm >/dev/null 2>&1; then
    # Use ci if available for reproducible installs
    if [ -f package-lock.json ]; then
      npm ci --no-audit --prefer-offline
    else
      npm install --no-audit --prefer-offline
    fi
    if npm test --silent; then
      echo "Frontend tests passed."
    else
      echo "Frontend tests failed."
      exit 1
    fi
  else
    echo "npm not found, skipping frontend tests."
  fi
else
  echo "No frontend test setup found. Skipping frontend tests."
fi


