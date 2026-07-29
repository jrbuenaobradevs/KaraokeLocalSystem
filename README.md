# Videoke Karaoke System

This repository contains an offline LAN-based karaoke system with a FastAPI backend and React frontend.

## Project Structure

- `backend/` — Python API, database, media scanning, playback controller
- `frontend/server-dashboard/` — Admin dashboard served by the karaoke server
- `frontend/client-ui/` — Mobile browser UI for song selection and queue requests
- `media/` — Local `.webm` karaoke files
- `backups/` — Database backups and exports
- `tests/` — Automated backend and frontend tests

## Phase 1: Setup

1. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate the virtual environment:
   - Windows: `.
   ```
3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Install frontend dependencies from each app folder:
   ```bash
   cd frontend/server-dashboard && npm install
   cd ../client-ui && npm install
   ```

## Notes

- The backend will scan `media/` for `.webm` files.
- The frontend apps are configured with Vite and Tailwind CSS.
- All services are intended to run without internet access.
