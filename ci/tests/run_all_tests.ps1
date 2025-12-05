Write-Host "=== Running all CI tests (PowerShell) ==="
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Try to run shell scripts if bash is available
if (Get-Command bash -ErrorAction SilentlyContinue) {
    & bash -lc "$here/run_all_tests.sh"
    exit $LASTEXITCODE
}

# Fallback: run backend tests via python/pytest if available
if (Test-Path "$here\..\backend") {
    Push-Location "$here\..\backend"
    if (Get-Command pytest -ErrorAction SilentlyContinue) {
        pytest -q
    } else {
        python -m pytest -q
    }
    Pop-Location
}

# Fallback frontend: run npm test if available
if (Test-Path "$here\..\frontend\package.json") {
    Push-Location "$here\..\frontend"
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm ci
        npm test --silent
    } else {
        Write-Host "npm not found; skipping frontend tests"
    }
    Pop-Location
}

Write-Host "=== PowerShell test runner finished ==="


