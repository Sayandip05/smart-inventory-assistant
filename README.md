# Smart Inventory Assistant

AI-assisted inventory management for healthcare supply chains.

## Quick Start

### 1. Backend

```bash
# Clone and setup
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Seed sample data
python ..\database\seed_data.py

# Run server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend\main-dashboard
npm install
npm run dev
```

### 3. URLs

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |

---

## Environment Variables

Create `backend/.env` from `.env.example`:

```env
DATABASE_PATH=../database/smart_inventory.db
ENVIRONMENT=development
GROQ_API_KEY=<your-key>
SARVAM_API_KEY=<your-key>
LANGCHAIN_API_KEY=<optional>
CORS_ORIGINS=http://localhost:5173
```

---

## Repository Structure

```
smart-inventory-assistant/
├── backend/
│   └── app/
│       ├── main.py                              # FastAPI entry point
│       ├── api/
│       │   ├── routes/
│       │   │   ├── analytics.py                # Heatmap, alerts, summary
│       │   │   ├── chat.py                    # Chatbot query, history, transcription
│       │   │   ├── inventory.py               # Locations, items, transactions
│       │   │   └── requisition.py              # Create, approve, reject
│       │   └── schemas/
│       │       ├── chat_schemas.py
│       │       ├── inventory_schemas.py
│       │       └── requisition_schemas.py
│       ├── application/                        # Business logic
│       │   ├── agent_tools.py                 # LangGraph @tool wrappers
│       │   ├── analytics_service.py
│       │   ├── inventory_service.py
│       │   └── requisition_service.py
│       ├── domain/                            # Pure logic (no framework deps)
│       │   ├── calculations.py                 # Reorder formula, health colors
│       │   └── agent/prompts.py              # System prompt text
│       ├── infrastructure/                    # External integrations
│       │   ├── database/
│       │   │   ├── connection.py             # SQLAlchemy engine/session
│       │   │   ├── models.py                # ORM classes
│       │   │   ├── queries.py               # Complex SQL (stock health, alerts)
│       │   │   ├── inventory_repo.py
│       │   │   └── requisition_repo.py
│       │   └── vector_store/
│       │       └── vector_store.py           # ChromaDB semantic memory
│       └── core/                             # Framework plumbing
│           ├── config.py                     # Settings from .env
│           ├── dependencies.py               # FastAPI Depends() factories
│           ├── error_handlers.py
│           ├── exceptions.py
│           ├── logging_config.py
│           └── middleware/request_logger.py
├── database/
│   ├── schema.sql                           # DB schema reference
│   ├── seed_data.py                        # Sample data
│   └── smart_inventory.db                   # SQLite file
├── frontend/main-dashboard/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── admin/                      # Dashboard, Inventory, Requisitions, Chatbot
│   │   │   ├── staff/                      # StaffRequisition
│   │   │   └── vendor/                     # DataEntry
│   │   ├── components/layout/              # AdminLayout, Sidebar
│   │   └── services/api.js                  # Axios HTTP client
│   └── package.json
├── docs/
│   ├── memory.md                            # Implementation status & roadmap
│   ├── system-architecture.md               # Architecture, layers, ADR summary
│   ├── HLD.md                              # Modules, APIs, entities, user journeys
│   ├── LLD.md                              # Schema, sequence diagrams, edge cases
│   └── deployment.md                        # Docker, CI/CD, environment configs
├── Dockerfile
├── docker-compose.yml
├── cicd.yaml
├── requirements.txt
└── README.md
```

---

## Architecture

Clean Architecture with strict layer separation:

| Layer | Rule | Examples |
|-------|------|----------|
| `domain/` | Zero framework imports | `calculations.py`, `prompts.py` |
| `infrastructure/` | Only domain + stdlib | `connection.py`, `models.py`, `vector_store.py` |
| `application/` | Calls both domain + infra | `*_service.py`, `agent_tools.py` |
| `api/` | Only calls application + core | `routes/`, `schemas/` |

---

## Module Audit (8/27 Implemented)

See `docs/memory.md` for the full audit table and phased roadmap.

Key implemented:
- FastAPI REST API with 4 route groups
- SQLAlchemy ORM + Repository pattern
- LangGraph AI agent with ChromaDB semantic memory
- Structured logging + global exception handling

Pending (Phase 1): JWT auth, role-based access, rate limiting, tests

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, Pydantic |
| AI | LangGraph, Groq (LLM), ChromaDB (memory) |
| Speech | Sarvam AI API |
| Frontend | React, Vite, Tailwind |
| Database | SQLite (dev) / PostgreSQL (prod) |

---

## Key Notes

- Role boundaries in the frontend (vendor/staff/admin) are UX-level only — backend authorization is pending Phase 1.
- `Dockerfile`, `docker-compose.yml`, and `cicd.yaml` are placeholders — full production implementation is Phase 5.
- See `docs/memory.md` for detailed implementation status and `docs/deployment.md` for deployment guide.
