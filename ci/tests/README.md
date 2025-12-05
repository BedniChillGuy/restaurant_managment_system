# CI tests

This directory contains small helper scripts to run the project's CI tests locally or inside CI runners.

Files
- `run_backend_tests.sh` — runs Python backend tests using `pytest` when available.
- `run_frontend_tests.sh` — installs frontend dependencies and runs `npm test` when `package.json` is present.
- `run_all_tests.sh` — runs backend and frontend shell scripts sequentially.
- `run_all_tests.ps1` — PowerShell runner that calls the shell runner if `bash` exists, otherwise runs fallback commands.

Usage
- On Linux/macOS or in CI:
  ```bash
  ci/tests/run_all_tests.sh
  ```

- On Windows (PowerShell):
  ```powershell
  .\ci\tests\run_all_tests.ps1
  ```

Notes
- Scripts are intentionally conservative: they skip components that are not present to make them safe for monorepos where not every job builds every component.
- These scripts do not install system-level dependencies (Python, Node, npm). Ensure CI runners provide required runtimes.


