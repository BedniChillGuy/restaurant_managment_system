#!/bin/sh
set -e

echo "=== Running frontend tests ==="

# 1) Python-based smoke‑тесты для статического фронтенда
if ls frontend/tests/*test*.py >/dev/null 2>&1; then
  if command -v pytest >/dev/null 2>&1; then
    echo "Running Python frontend tests with pytest..."
    pytest -q frontend/tests
  else
    echo "pytest not found; skipping Python frontend tests."
  fi
else
  echo "No Python frontend tests found."
fi

# 2) Если когда‑нибудь появится полноценный Node‑фронтенд с package.json,
#    этот блок позволит запускать npm‑тесты.
if [ -d "frontend" ] && [ -f frontend/package.json ]; then
  cd frontend
  if command -v npm >/dev/null 2>&1; then
    if [ -f package-lock.json ]; then
      npm ci --no-audit --prefer-offline
    else
      npm install --no-audit --prefer-offline
    fi
    if npm test --silent; then
      echo "Frontend npm tests passed."
    else
      echo "Frontend npm tests failed."
      exit 1
    fi
  else
    echo "npm not found, skipping npm-based frontend tests."
  fi
else
  echo "No Node-based frontend project detected (package.json missing); skipping npm tests."
fi


