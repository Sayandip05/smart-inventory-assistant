# Smart Inventory Assistant

Lightweight FastAPI + SQLite backend for healthcare inventory insights. This README is a quick scaffold; fill in details as the app grows.

## Tech
- FastAPI, SQLAlchemy
- SQLite (local dev), dotenv for config
- Optional Groq API key (future AI features)

## Project Layout
- `backend/app/main.py` FastAPI entrypoint with basic health routes.
- `backend/app/config.py` Settings loaded from `.env` (DATABASE_PATH, GROQ_API_KEY, CORS).
- `backend/app/database/connection.py` SQLite engine/session factory.
- `backend/app/database/models.py` ORM models for locations, items, transactions.
- `backend/app/database/queries.py` stock health/alerts/heatmap helpers.
- `database/schema.sql` schema definition; `database/seed_data.py` sample data loader; `database/smart_inventory.db` local DB (gitignored).
- `.env.example` sample environment file; copy to `.env` and adjust.
- `Dockerfile` placeholder; `docker-compose.yml` intentionally empty for now.
- `.dockerignore` and `.gitignore` tuned for Python/SQLite artifacts.

## Quickstart (local)
```bash
python -m venv venv && venv/Scripts/activate  # or source venv/bin/activate on *nix
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.app.main:app --reload
```

## Notes
- DATABASE_PATH defaults to `../database/smart_inventory.db`; override in `.env` if needed.
- Add GROQ_API_KEY later when wiring LLM features.
- Docker/compose files are placeholders until the deployment plan is finalized.

