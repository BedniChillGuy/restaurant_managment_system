#!/bin/sh
set -e

echo "=== Running backend tests ==="

if [ -d "backend" ]; then
  # prefer pytest if project looks like a Python project
  if [ -f backend/pyproject.toml ] || [ -f backend/requirements.txt ] || [ -d backend/tests ]; then
    cd backend
    if command -v pytest >/dev/null 2>&1; then
      pytest -q
    else
      echo "pytest not found, trying python -m pytest"
      python -m pytest -q
    fi
  else
    echo "No backend test configuration or tests directory found. Skipping backend tests."
  fi
else
  echo "No backend directory found. Skipping backend tests."
fi


