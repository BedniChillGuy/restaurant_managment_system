#!/bin/sh
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Running all CI tests ==="
sh "$DIR/run_backend_tests.sh"
sh "$DIR/run_frontend_tests.sh"
echo "=== All CI tests finished ==="


