# Smart Inventory Assistant

AI-assisted inventory management for healthcare supply chains.

## Current Snapshot

- Architecture: Modular monolith (FastAPI backend + React frontend)
- Code scan date: March 15, 2026
- Module progress (1-27):
  - Implemented: 8
  - Partially implemented: 6
  - Not implemented: 13

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- AI: LangGraph, LangChain, Groq-compatible LLM endpoint
- Memory: SQLite chat history + ChromaDB semantic memory
- Speech-to-text: Sarvam AI API
- Frontend: React + Vite + Tailwind
- Infra status: Docker/Compose/CI placeholders (not production ready)

## High Level Design (HLD)

### 1) System Context

- Vendor UI submits inventory transactions.
- Staff UI creates requisitions.
- Admin UI monitors analytics, approves/rejects requisitions, and uses AI chat.
- FastAPI serves all business APIs.
- SQLite stores transactional and chat relational data.
- ChromaDB stores long-term semantic chat memory.
- External APIs: Groq-compatible LLM and Sarvam speech-to-text.

### 2) Backend Architecture

The backend follows a layered modular monolith design:

- API Routes: request parsing and HTTP contract.
- Services: business logic and orchestration.
- Repositories: database access abstraction.
- Core: cross-cutting concerns (config, exceptions, handlers, logging, DI).
- Middleware: request logging and correlation headers.

#### Layer Responsibilities

| Layer | Main files | Responsibility |
|---|---|---|
| Entry point | `backend/app/main.py` | App bootstrap, middleware, router registration |
| Routes | `backend/app/api/routes/*.py` | Endpoint contracts and request validation |
| Services | `backend/app/services/*.py` | Domain logic for inventory, requisition, analytics, chat |
| Repositories | `backend/app/repositories/*.py` | Encapsulated SQLAlchemy queries |
| Core | `backend/app/core/*.py` | Exceptions, handlers, logging config, dependency factories |
| Persistence | `backend/app/database/*.py` | Engine/session/models/query helpers |

### 3) Primary Request Flows

#### A) Inventory/Requisition Flow

1. Frontend calls `/api/inventory/*` or `/api/requisition/*`.
2. Route validates payload using Pydantic models.
3. Service applies business rules.
4. Repository executes SQLAlchemy operations.
5. Standard JSON response is returned.

#### B) AI Chat Flow

1. Frontend calls `/api/chat/query`.
2. Agent loads recent chat history from SQLite (`chat_sessions`, `chat_messages`).
3. Agent optionally retrieves semantic context from ChromaDB.
4. LLM can call inventory tools backed by SQLAlchemy queries.
5. Response is saved to SQLite and optionally to ChromaDB.

### 4) Data Model (Implemented)

Main ORM tables:

- `locations`
- `items`
- `inventory_transactions`
- `requisitions`
- `requisition_items`
- `chat_sessions`
- `chat_messages`

Additional SQL object:

- `stock_health` view in `database/schema.sql`

### 5) Operational Baseline

Implemented:

- Global exception handling and custom exception classes
- Structured logging and request ID/process-time headers
- Environment-driven configuration

Not yet implemented:

- Auth and backend RBAC enforcement
- Rate limiting and broader API hardening
- Lifespan startup/shutdown resource cleanup
- Production containerization and CI/CD
- Automated tests

## Module Audit (1-27)

| # | Module | Status |
|---|---|---|
| 1 | HTTP and How the Web Works | Implemented |
| 2 | Routing and Path Operations | Implemented |
| 3 | JSON and Data Serialization | Implemented |
| 4 | Authentication and Authorization | Not implemented |
| 5 | Data Validation (Pydantic) | Implemented |
| 6 | Application Architecture | Implemented |
| 7 | API Design Best Practices | Partial |
| 8 | Databases and ORMs (SQLAlchemy) | Implemented |
| 9 | Caching (Redis) | Not implemented |
| 10 | Task Queues (Celery) | Not implemented |
| 11 | Error Handling and Exception Management | Implemented |
| 12 | Configuration Management | Implemented |
| 13 | Logging and Observability (LangSmith, Prometheus) | Partial |
| 14 | Graceful Shutdown and Lifespan | Not implemented |
| 15 | Backend Security (JWT, HMAC, Rate Limiting, BOLA/BFLA, XSS) | Not implemented |
| 16 | Scaling and Performance Part A | Partial |
| 17 | Scaling and Performance Part B | Not implemented |
| 18 | Concurrency and Parallelism | Partial |
| 19 | Testing and Code Quality | Not implemented |
| 20 | Object Storage and Large Files (AWS S3, Boto3, pre-signed URLs) | Not implemented |
| 21 | Real-Time Systems (WebSockets, Redis Pub/Sub) | Not implemented |
| 22 | Webhooks (HMAC verification, idempotency) | Not implemented |
| 23 | Advanced Search (Elasticsearch, BM25) | Not implemented |
| 24 | Transactional Emails and Background Tasks | Not implemented |
| 25 | API Documentation (OpenAPI, Swagger, ReDoc, response_model) | Partial |
| 26 | The 12-Factor App | Partial |
| 27 | DevOps and Containerization | Not implemented |

## Repository Structure

```text
smart-invantory-assistant/
  backend/
    app/
      api/routes/
      core/
      database/
      middleware/
      repositories/
      services/
      utils/
  frontend/
    main-dashboard/
  database/
    schema.sql
    seed_data.py
  README.md
  what is implemented.md
  what will be implemented.md
```

## Local Run

### Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python database/seed_data.py
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend/main-dashboard
npm install
npm run dev
```

### URLs

- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Key Notes

- Role boundaries in the frontend (vendor/staff/admin) are UX-level only right now; backend authz is pending.
- `Dockerfile`, `docker-compose.yml`, and `cicd.yaml` are placeholders and need full implementation before production use.
- See `what is implemented.md` for evidence-backed status and `what will be implemented.md` for the prioritized roadmap.
