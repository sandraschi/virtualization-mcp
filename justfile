set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# ── Default ──────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Setup ────────────────────────────────────────────────────────────────────

# Install everything (Python venv + npm deps)
install:
    cd {{justfile_directory()}}
    uv sync
    cd webapp\\frontend
    npm install

# Install just the Python backend
install-py:
    cd {{justfile_directory()}}
    uv sync

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
    cd {{justfile_directory()}}
    uv run uvicorn virtualization_mcp.web.app:app --reload --port 10701 --host 0.0.0.0

# Start just the frontend dev server (port 10700)
start-frontend:
    cd {{justfile_directory()}}\\webapp\\frontend
    bun run dev

# ── Test ──────────────────────────────────────────────────────────────────────

# Run all core tests (62 tests, mock-only, no VBox needed)
test:
    cd {{justfile_directory()}}
    $env:PYTHONPATH = "src"
    uv run pytest tests/ -v --tb=short -o "addopts="

# Run specific test file
test-file file:
    cd {{justfile_directory()}}
    $env:PYTHONPATH = "src"
    uv run pytest {{file}} -v --tb=short -o "addopts="

# ── Quality ───────────────────────────────────────────────────────────────────

lint:
    powershell.exe -NoProfile -File "{{justfile_directory()}}/scripts/lint.ps1"

fix:
    powershell.exe -NoProfile -File "{{justfile_directory()}}/scripts/fix.ps1"

check-unicode:
    powershell.exe -NoProfile -File '{{justfile_directory()}}\\scripts\\check-unicode-safe.ps1'

# ── Build ─────────────────────────────────────────────────────────────────────

# Build frontend for production
build:
    cd {{justfile_directory()}}\\webapp\\frontend
    bun run build

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
    powershell.exe -NoProfile -File "{{justfile_directory()}}/scripts/clean.ps1"

# ── Tauri Native ───────────────────────────────────────────────────────────────

# Build Tauri native desktop app (full pipeline: frontend + PyInstaller + NSIS)
build-native:
    cd {{justfile_directory()}}\\native
    .\\build.ps1

# Build Tauri native (debug, skip PyInstaller)
build-native-debug:
    cd {{justfile_directory()}}\\native
    $env:Path = "$env:USERPROFILE\\.cargo\\bin;$env:Path"
    npx @tauri-apps/cli build --debug

# ── Playwright E2E ─────────────────────────────────────────────────────

e2e-install:
    powershell.exe -NoProfile -File "{{justfile_directory()}}/scripts/e2e-install.ps1"

e2e:
    powershell.exe -NoProfile -File "{{justfile_directory()}}/scripts/e2e.ps1"
