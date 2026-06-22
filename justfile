set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

# ── Default ──────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Setup ────────────────────────────────────────────────────────────────────

# Install everything (Python venv + npm deps)
install:
    cd {{justfile_directory()}}
    python -m venv .venv
    .venv\\Scripts\\pip install -e .
    cd webapp\\frontend
    npm install

# Install just the Python backend
install-py:
    cd {{justfile_directory()}}
    python -m venv .venv
    .venv\\Scripts\\pip install -e .

# Install just the frontend
install-frontend:
    cd {{justfile_directory()}}\\webapp\\frontend
    npm install

# ── Run ──────────────────────────────────────────────────────────────────────

# Start the web dashboard (backend + frontend)
start:
    cd {{justfile_directory()}}\\webapp
    .\\start.ps1

# Start just the backend API (port 10701)
start-backend:
    cd {{justfile_directory()}}\\webapp\\backend
    .venv\\Scripts\\uvicorn app.main:app --reload --port 10701 --host 0.0.0.0

# Start just the frontend dev server (port 10700)
start-frontend:
    cd {{justfile_directory()}}\\webapp\\frontend
    npm run dev

# ── Test ──────────────────────────────────────────────────────────────────────

# Run all core tests (62 tests, mock‑only, no VBox needed)
test:
    cd {{justfile_directory()}}
    $env:PYTHONPATH="src"
    uv run pytest tests/ -v --tb=short -o "addopts="

# Run specific test file
test-file file:
    cd {{justfile_directory()}}
    $env:PYTHONPATH="src"
    uv run pytest {{file}} -v --tb=short -o "addopts="

# ── Quality ───────────────────────────────────────────────────────────────────

lint:
    pwsh -NoProfile -File "{{justfile_directory()}}/scripts/lint.ps1"

fix:
    pwsh -NoProfile -File "{{justfile_directory()}}/scripts/fix.ps1"

check-unicode:
    pwsh -NoProfile -File '{{justfile_directory()}}\\scripts\\check-unicode-safe.ps1'

# ── Build ─────────────────────────────────────────────────────────────────────

# Build frontend for production
build:
    cd {{justfile_directory()}}\\webapp\\frontend
    npm run build

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
    pwsh -NoProfile -File "{{justfile_directory()}}/scripts/clean.ps1"

# ── Tauri Native ───────────────────────────────────────────────────────────────

# Build Tauri native desktop app (full pipeline: frontend + backend)
build-native:
    # (original build‑native steps remain unchanged)

# ── Playwright E2E ─────────────────────────────────────────────────────

e2e-install:
    pwsh -NoProfile -File "{{justfile_directory()}}/scripts/e2e-install.ps1"

e2e:
    pwsh -NoProfile -File "{{justfile_directory()}}/scripts/e2e.ps1"
