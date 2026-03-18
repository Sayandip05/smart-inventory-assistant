# Data Flow Diagrams

**Project:** Smart Inventory Assistant  
**Date:** March 17, 2026

---

## 1. Overall Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              OVERALL DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                                USERS                                         │   │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │   │
│   │   │ Vendor   │    │ Staff    │    │ Admin    │    │   AI     │             │   │
│   │   │          │    │          │    │          │    │ (Groq)   │             │   │
│   │   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘             │   │
│   │        │                │                │                │                     │   │
│   └────────┼────────────────┼────────────────┼────────────────┼─────────────────────┘   │
│            │                │                │                │                         │
│            │   DATA ENTRY  │                │                │   API CALLS            │
│            ▼                ▼                ▼                ▼                         │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                         FRONTEND (React)                                     │   │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │   │
│   │   │ DataEntry│    │Requisition│   │Dashboard │    │ Chatbot  │             │   │
│   │   │ Page     │    │ Page      │    │ Page     │    │ Page     │             │   │
│   │   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘             │   │
│   │        │                │                │                │                     │   │
│   │        └────────────────┴────────────────┼────────────────┘                     │   │
│   │                                         │                                       │   │
│   └─────────────────────────────────────────┼───────────────────────────────────────┘   │
│                                                 │                                       │
│                                                 ▼ HTTP Requests                        │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                         BACKEND (FastAPI)                                    │   │
│   │                                                                               │   │
│   │   ┌──────────────────────────────────────────────────────────────────────┐  │   │
│   │   │                         API ROUTES                                    │  │   │
│   │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │   │
│   │   │  │ /inventory  │  │/requisition │  │  /chat     │  │/analytics  │ │  │   │
│   │   │  │   routes    │  │   routes    │  │  routes    │  │  routes    │ │  │   │
│   │   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │  │   │
│   │   └─────────┼────────────────┼────────────────┼────────────────┼────────┘  │   │
│   │             │                │                │                │              │   │
│   │             └────────────────┴────────────────┼────────────────┘              │   │
│   │                                          │                                    │   │
│   │                                          ▼                                    │   │
│   │   ┌──────────────────────────────────────────────────────────────────────┐  │   │
│   │   │                        SERVICE LAYER                                   │  │   │
│   │   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │   │
│   │   │  │ Inventory       │  │ Requisition    │  │ AI Agent            │   │  │   │
│   │   │  │ Service         │  │ Service        │  │ (LangGraph)         │   │  │   │
│   │   │  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘   │  │   │
│   │   └───────────┼───────────────────┼──────────────────────┼───────────────┘  │   │
│   │               │                   │                      │                    │   │
│   │               └───────────────────┴──────────────────────┘                    │   │
│   │                                   │                                             │   │
│   │                                   ▼                                             │   │
│   │   ┌──────────────────────────────────────────────────────────────────────┐  │   │
│   │   │                      REPOSITORY LAYER                                  │  │   │
│   │   │  ┌─────────────────┐  ┌─────────────────┐                             │  │   │
│   │   │  │ Inventory       │  │ Requisition     │                             │  │   │
│   │   │  │ Repository      │  │ Repository      │                             │  │   │
│   │   │  └────────┬────────┘  └────────┬────────┘                             │  │   │
│   │   └───────────┼───────────────────┼───────────────────────────────────────┘  │   │
│   │               │                   │                                           │   │
│   │               └───────────────────┴───────────────────────────────────────────┘   │
│   │                                   │                                               │
│   │                                   ▼                                               │
│   │   ┌──────────────────────────────────────────────────────────────────────┐   │
│   │   │                     DATABASE LAYER                                     │   │
│   │   │   ┌──────────────────────┐    ┌────────────────────────────────────┐   │   │
│   │   │   │      SQLite         │    │          ChromaDB                  │   │   │
│   │   │   │                      │    │                                   │   │   │
│   │   │   │ locations           │    │   chat_memory collection           │   │   │
│   │   │   │ items               │    │   (embeddings + metadata)          │   │   │
│   │   │   │ inventory_transactions  │                                   │   │   │
│   │   │   │ requisitions        │    │                                   │   │   │
│   │   │   │ requisition_items   │    │                                   │   │   │
│   │   │   │ chat_sessions       │    │                                   │   │   │
│   │   │   │ chat_messages       │    │                                   │   │   │
│   │   │   │ stock_health (view) │    │                                   │   │   │
│   │   │   └──────────────────────┘    └────────────────────────────────────┘   │   │
│   │   │                                                                    │   │
│   │   └────────────────────────────────────────────────────────────────────┘   │
│   │                                                                               │
│   └───────────────────────────────────────────────────────────────────────────────┘
│                                                                                      │
│                                    │                                                │
│                                    │ EXTERNAL API CALLS                             │
│                                    ▼                                                │
│   ┌───────────────────────────────────────────────────────────────────────────────┐  │
│   │                         EXTERNAL SERVICES                                      │  │
│   │  ┌────────────────┐    ┌────────────────┐    ┌────────────────────────────┐ │  │
│   │  │  Groq LLM     │    │  Sarvam AI    │    │   LangSmith (Optional)    │ │  │
│   │  │  API          │    │  Speech-to-Text│    │   Observability          │ │  │
│   │  └────────────────┘    └────────────────┘    └────────────────────────────┘ │  │
│   │                                                                                │  │
│   └────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Inventory Transaction Flow

```
┌──────────┐     POST /api/inventory/transaction     ┌──────────┐
│          │  {location_id, item_id, date,          │          │
│ Vendor   │   received, issued, notes}             │ FastAPI  │
│ Browser  │ ───────────────────────────────────────▶│  Server  │
│          │                                          │          │
└──────────┘                                          └────┬─────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ Validate Input  │
                                                 │ (Pydantic)     │
                                                 └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ InventoryService│
                                                 │ .add_transaction│
                                                 └────────┬────────┘
                                                          │
                        ┌───────────────────────────────┬─┘
                        │                               │
                        ▼                               ▼
               ┌──────────────────┐         ┌──────────────────┐
               │ Get Previous     │         │ Calculate        │
               │ Transaction     │         │ Closing Stock    │
               │ (Repository)    │         │ opening +        │
               └────────┬─────────┘         │ received - issued│
                        │                   └────────┬─────────┘
                        │                            │
                        ▼                            ▼
               ┌──────────────────────────────────────────────┐
               │         InventoryRepository                   │
               │         .create_transaction()                 │
               └────────────────────┬───────────────────────────┘
                                    │
                                    ▼
                           ┌────────────────┐
                           │   SQLite DB   │
                           │ INSERT INTO    │
                           │ inventory_     │
                           │ transactions   │
                           └────────────────┘
                                    │
                                    ▼
                           ┌────────────────┐
                           │ Return Success │
                           │ Response       │
                           └────────────────┘
                                    │
                                    ▼
                           ┌────────────────┐
                           │ Frontend       │
                           │ Updates UI     │
                           └────────────────┘
```

---

## 3. Requisition Flow

```
┌──────────┐     POST /api/requisition/create    ┌──────────┐
│          │  {location_id, items:[],           │          │
│ Staff    │   urgency, department}             │ FastAPI  │
│ Browser  │ ──────────────────────────────────▶│  Server  │
│          │                                     │          │
└──────────┘                                     └────┬─────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │ Validate Input  │
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │RequisitionService│
                                            │.create()        │
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │ Generate Req #  │
                                            │ REQ-YYYYMMDD-XXX│
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │ Save Requisition│
                                            │ + Items         │
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │  Status:        │
                                            │  PENDING        │
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │ Return Response│
                                            └────────────────┘
                                                     │
                                                     ▼
                                            ┌────────────────┐
                                            │ Frontend shows │
                                            │ Success Message│
                                            └────────────────┘
```

---

## 4. Requisition Approval Flow

```
┌──────────┐     PUT /api/requisition/{id}/approve  ┌──────────┐
│          │  {approved_by, notes}                   │          │
│ Admin    │ ──────────────────────────────────────▶│ FastAPI  │
│ Browser  │                                         │  Server  │
│          │                                         └────┬─────┘
└──────────┘                                              │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Load Requisition│
                                                │ from Database   │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Validate Status │
                                                │ (must be        │
                                                │  PENDING)       │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │RequisitionService│
                                                │.approve()       │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Update Status   │
                                                │ to APPROVED     │
                                                │ Set approved_by │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ (Future: Adjust │
                                                │  Inventory)     │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌────────────────┐
                                                │ Return Success │
                                                └────────────────┘
```

---

## 5. AI Chat Flow

```
┌──────────┐     POST /api/chat/query           ┌──────────┐
│          │  {question, conversation_id?}      │          │
│ Admin    │ ──────────────────────────────────▶│ FastAPI  │
│ Browser  │                                     │  Server  │
│          │                                     └────┬─────┘
└──────────┘                                           │
                                                       ▼
                                              ┌─────────────────┐
                                              │ Validate Input  │
                                              │ (min 3 chars)  │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ InventoryAgent  │
                                              │ .query()       │
                                              └────────┬────────┘
                                                       │
                       ┌───────────────────────────────┼───────────────────────┐
                       │                               │                       │
                       ▼                               ▼                       ▼
              ┌──────────────────┐         ┌──────────────────┐    ┌──────────────────┐
              │ Load Chat History│         │ Search ChromaDB  │    │ Build System    │
              │ from SQLite      │         │ Semantic Memory  │    │ Prompt          │
              │ (last 10 msgs)  │         │                  │    │ + Context       │
              └────────┬─────────┘         └────────┬─────────┘    └────────┬─────────┘
                       │                            │                        │
                       └────────────────────────────┼────────────────────────┘
                                                    │
                                                    ▼
                                           ┌──────────────────┐
                                           │ Invoke LangGraph │
                                           │ Workflow         │
                                           └────────┬─────────┘
                                                    │
                       ┌───────────────────────────┬┘
                       │                           │
                       ▼                           ▼
              ┌──────────────────┐     ┌──────────────────┐
              │   LLM Decision   │────▶│   Tool Call?     │
              │   (Agent Node)   │     │   (YES/NO)       │
              └────────┬─────────┘     └────────┬─────────┘
                       │                        │
                       │                        ▼
                       │               ┌──────────────────┐
                       │               │ Execute Tool     │
                       │               │ (SQLAlchemy)     │
                       │               └────────┬─────────┘
                       │                        │
                       │                        ▼
                       │               ┌──────────────────┐
                       │               │ Return Tool      │
                       │               │ Results          │
                       │               └────────┬─────────┘
                       │                        │
                       │◀───────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Generate Final   │
              │ Response         │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Save to SQLite   │
              │ (session + msg)  │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Save to ChromaDB │
              │ (embedding)      │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Return Response  │
              │ to Frontend      │
              └──────────────────┘
```

---

## 6. Analytics Data Flow

```
┌──────────┐     GET /api/analytics/dashboard/stats ┌──────────┐
│          │                                         │          │
│ Admin    │ ───────────────────────────────────────▶│ FastAPI  │
│ Browser  │                                         │  Server  │
│          │                                         └────┬─────┘
└──────────┘                                               │
                                                         ▼
                                                ┌─────────────────┐
                                                │AnalyticsService │
                                                │.get_dashboard   │
                                                │_stats()         │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Query           │
                                                │ stock_health    │
                                                │ VIEW            │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Aggregate Data  │
                                                │ - By Category   │
                                                │ - By Location   │
                                                │ - By Status    │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Transform to    │
                                                │ Chart Format    │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Return JSON     │
                                                │ { category_     │
                                                │   distribution, │
                                                │   low_stock_,   │
                                                │   location_     │
                                                │   stock, ... }  │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Frontend Renders│
                                                │ Charts          │
                                                └─────────────────┘
```

---

## 7. Speech-to-Text Flow

```
┌──────────┐     POST /api/chat/transcribe     ┌──────────┐
│          │  (Audio File: wav/mp3)            │          │
│ Admin    │ ──────────────────────────────────▶│ FastAPI  │
│ Browser  │                                     │  Server  │
│          │                                     └────┬─────┘
└──────────┘                                           │
                                                      ▼
                                             ┌─────────────────┐
                                             │ Read Audio File │
                                             │ (Binary)        │
                                             └────────┬────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │ Sarvam AI API   │
                                             │ POST /speech-to │
                                             │ -text-translate │
                                             └────────┬────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │ Get Transcript │
                                             │ (English Text) │
                                             └────────┬────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │ Return Text     │
                                             │ to Frontend    │
                                             └─────────────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │ Auto-fill      │
                                             │ Chat Input     │
                                             └─────────────────┘
```

---

## 8. Data Transformation Summary

| Flow | Input | Processing | Output |
|------|-------|------------|--------|
| Inventory Transaction | Form data (JSON) | Calculate closing_stock | Saved transaction |
| Requisition Create | Items array | Generate ID, set PENDING | New requisition |
| Requisition Approve | Req ID + approver | Update status | Approved requisition |
| AI Chat Query | Question text | LLM inference + tools | Natural language response |
| Analytics | None (read) | Aggregate from VIEW | Chart-ready JSON |
| Transcription | Audio file | Sarvam API call | Text transcript |
