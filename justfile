set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Default ──────────────────────────────────────────────────────────────────

# Show available recipes
default:
    @just --list

# ── Setup ────────────────────────────────────────────────────────────────────

# Install everything (Python venv + npm deps)
install:
    cd {{justfile_directory()}}
    python -m venv .venv
    .venv\Scripts\pip install -e .
    cd webapp\frontend
    npm install

# Install just the Python backend
install-py:
    cd {{justfile_directory()}}
    python -m venv .venv
    .venv\Scripts\pip install -e .

# Install just the frontend
install-frontend:
    cd {{justfile_directory()}}\webapp\frontend
    npm install

# ── Run ──────────────────────────────────────────────────────────────────────

# Start the web dashboard (backend + frontend)
start:
    cd {{justfile_directory()}}\webapp
    .\start.ps1

# Start just the backend API (port 10701)
start-backend:
    cd {{justfile_directory()}}\webapp\backend
    .venv\Scripts\uvicorn app.main:app --reload --port 10701 --host 0.0.0.0

# Start just the frontend dev server (port 10700)
start-frontend:
    cd {{justfile_directory()}}\webapp\frontend
    npm run dev

# ── Test ──────────────────────────────────────────────────────────────────────

# Run all core tests (62 tests, mock-only, no VBox needed)
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

# Lint check (ruff + biome)
lint:
    cd {{justfile_directory()}}
    uv run ruff check src/
    cd webapp\frontend
    npx @biomejs/biome ci .

# Auto-fix lint issues
fix:
    cd {{justfile_directory()}}
    uv run ruff check src/ --fix --unsafe-fixes
    uv run ruff format src/
    cd webapp\frontend
    npx @biomejs/biome check --write .

# Check for unicode dashes/smart quotes that break PowerShell
check-unicode:
    pwsh -NoProfile -File '{{justfile_directory()}}\scripts\check-unicode-safe.ps1'

# ── Build ─────────────────────────────────────────────────────────────────────

# Build frontend for production
build:
    cd {{justfile_directory()}}\webapp\frontend
    npm run build

# ── Clean ─────────────────────────────────────────────────────────────────────

# Remove build artifacts and cache
clean:
    cd {{justfile_directory()}}
    Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force src\__pycache__ -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force webapp\frontend\node_modules -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force webapp\frontend\dist -ErrorAction SilentlyContinue
    Remove-Item -Force .pytest_cache -ErrorAction SilentlyContinue
