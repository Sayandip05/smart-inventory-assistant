# High Level Design (HLD)

**Project:** Smart Inventory Assistant  
**Date:** March 17, 2026

---

## 1. Module Breakdown

### 1.1 Core Modules

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                MODULE OVERVIEW                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                           FRONTEND MODULES                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │  │
│  │  │ Vendor      │  │ Staff       │  │ Admin       │  │ Shared Components  │ │  │
│  │  │ DataEntry   │  │Requisition  │  │ Dashboard   │  │ (Layout, Sidebar) │ │  │
│  │  │ Page        │  │ Page        │  │ Page        │  │                    │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │  │
│  │  │ Inventory   │  │ Requisition │  │ Chatbot     │                         │  │
│  │  │ Page        │  │ Approval    │  │ Page        │                         │  │
│  │  │             │  │ Page        │  │             │                         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                         │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                           BACKEND MODULES                                      │  │
│  │  ┌─────────────────────────┐  ┌───────────────────────────────────────────┐  │  │
│  │  │ API Layer               │  │ Service Layer                           │  │  │
│  │  │ ┌───────────────────┐  │  │ ┌─────────────────────────────────────┐ │  │  │
│  │  │ │ /inventory routes │  │  │ │ InventoryService                   │ │  │  │
│  │  │ │ /requisition routes│  │  │ │ - add_transaction()                │ │  │  │
│  │  │ │ /chat routes      │  │  │ │ - bulk_add_transactions()         │ │  │  │
│  │  │ │ /analytics routes │  │  │ │ - get_location_items()            │ │  │  │
│  │  │ └───────────────────┘  │  │ └─────────────────────────────────────┘ │  │  │
│  │  │                         │  │ ┌─────────────────────────────────────┐ │  │  │
│  │  │                         │  │ │ RequisitionService                 │ │  │  │
│  │  │                         │  │ │ - create_requisition()             │ │  │  │
│  │  │                         │  │ │ - approve() / reject()             │ │  │  │
│  │  │                         │  │ │ - get_stats()                     │ │  │  │
│  │  │                         │  │ └─────────────────────────────────────┘ │  │  │
│  │  │                         │  │ ┌─────────────────────────────────────┐ │  │  │
│  │  │                         │  │ │ AnalyticsService                  │ │  │  │
│  │  │                         │  │ │ - get_heatmap()                   │ │  │  │
│  │  │                         │  │ │ - get_alerts()                    │ │  │  │
│  │  │                         │  │ │ - get_summary()                   │ │  │  │
│  │  │                         │  │ └─────────────────────────────────────┘ │  │  │
│  │  │                         │  │ ┌─────────────────────────────────────┐ │  │  │
│  │  │                         │  │ │ AI Agent Service                   │ │  │  │
│  │  │                         │  │ │ - query()                          │ │  │  │
│  │  │                         │  │ │ - get_conversation_history()      │ │  │  │
│  │  │                         │  │ └─────────────────────────────────────┘ │  │  │
│  │  └─────────────────────────┘  └───────────────────────────────────────────┘  │  │
│  │                                    │                                          │  │
│  │                                    ▼                                          │  │
│  │  ┌─────────────────────────┐  ┌───────────────────────────────────────────┐  │  │
│  │  │ Repository Layer       │  │ Core Layer                               │  │  │
│  │  │ ┌───────────────────┐  │  │ ┌─────────────────────────────────────┐ │  │  │
│  │  │ │InventoryRepository│  │  │ │ Config (Settings)                   │ │  │  │
│  │  │ │RequisitionRepository│ │  │ │ - DATABASE_PATH                    │ │  │  │
│  │  │ └───────────────────┘  │  │ │ - API Keys                         │ │  │  │
│  │  │                         │  │ └─────────────────────────────────────┘ │  │  │
│  │  │                         │  │ ┌─────────────────────────────────────┐ │  │  │
│  │  │                         │  │ │ Exceptions                         │ │  │  │
│  │  │                         │  │ │ - AppException                     │ │  │  │
│  │  │                         │  │ │ - NotFoundError                    │ │  │  │
│  │  │                         │  │ │ - ValidationError                  │ │  │  │
│  │  │                         │  │ └─────────────────────────────────────┘ │  │  │
│  │  └─────────────────────────┘  └───────────────────────────────────────────┘  │  │
│  │                                    │                                          │  │
│  │                                    ▼                                          │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        DATA LAYER                                      │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │  │
│  │  │  │  SQLite      │  │  ChromaDB    │  │  SQL Queries │              │  │  │
│  │  │  │  (ORM)      │  │  (Vector)    │  │  (Views)     │              │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │  │
│  │  └──────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                           │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Module Descriptions

| Module | Responsibility | Dependencies |
|--------|---------------|--------------|
| **Vendor DataEntry** | Form for entering inventory transactions | InventoryService, api.js |
| **Staff Requisition** | Create requisition requests | RequisitionService, api.js |
| **Admin Dashboard** | Display analytics charts | AnalyticsService, api.js |
| **Admin Inventory** | View/manage inventory | InventoryService, api.js |
| **Admin Requisitions** | Approve/reject requisitions | RequisitionService, api.js |
| **Admin Chatbot** | AI conversation interface | ChatService, api.js |
| **InventoryService** | Transaction CRUD, stock calculations | InventoryRepository |
| **RequisitionService** | Requisition workflow | RequisitionRepository, InventoryService |
| **AnalyticsService** | Data aggregation, statistics | SQL queries |
| **AI Agent Service** | LLM orchestration, tool calling | LangGraph, VectorMemory |
| **InventoryRepository** | Location/Item/Transaction CRUD | SQLAlchemy |
| **RequisitionRepository** | Requisition CRUD | SQLAlchemy |

---

## 2. API Surface (Summary)

### 2.1 Inventory APIs

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/api/inventory/locations` | GET | List all locations | Backend | Frontend |
| `/api/inventory/items` | GET | List all items | Backend | Frontend |
| `/api/inventory/location/{id}/items` | GET | Items at location | Backend | Frontend |
| `/api/inventory/stock/{location_id}/{item_id}` | GET | Current stock level | Backend | Frontend |
| `/api/inventory/transaction` | POST | Add transaction | Backend | Frontend |
| `/api/inventory/bulk-transaction` | POST | Bulk add transactions | Backend | Frontend |
| `/api/inventory/reset-data` | POST | Reset test data | Backend | Frontend |

### 2.2 Requisition APIs

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/api/requisition/create` | POST | Create requisition | Backend | Staff UI |
| `/api/requisition/list` | GET | List requisitions | Backend | Admin UI |
| `/api/requisition/{id}` | GET | Get requisition | Backend | Admin UI |
| `/api/requisition/stats` | GET | Requisition statistics | Backend | Admin UI |
| `/api/requisition/{id}/approve` | PUT | Approve requisition | Backend | Admin UI |
| `/api/requisition/{id}/reject` | PUT | Reject requisition | Backend | Admin UI |
| `/api/requisition/{id}/cancel` | PUT | Cancel requisition | Backend | Admin UI |

### 2.3 Analytics APIs

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/api/analytics/heatmap` | GET | Stock level matrix | Backend | Dashboard |
| `/api/analytics/alerts` | GET | Critical/warning items | Backend | Dashboard |
| `/api/analytics/summary` | GET | Overall statistics | Backend | Dashboard |
| `/api/analytics/dashboard/stats` | GET | Dashboard chart data | Backend | Dashboard |

### 2.4 Chat APIs

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/api/chat/query` | POST | Send AI question | Backend | Chatbot UI |
| `/api/chat/history/{id}` | GET | Get conversation | Backend | Chatbot UI |
| `/api/chat/sessions` | GET | List conversations | Backend | Chatbot UI |
| `/api/chat/suggestions` | GET | Question suggestions | Backend | Chatbot UI |
| `/api/chat/transcribe` | POST | Audio to text | Backend | Chatbot UI |

---

## 3. Major Data Entities

### 3.1 Entity Relationship

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Location    │────────▶│  Inventory   │◀────────│     Item     │
│              │  1:N    │ Transaction  │    N:1  │              │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ id           │         │ id           │         │ id           │
│ name         │         │ location_id  │         │ name         │
│ type         │         │ item_id      │         │ category     │
│ region       │         │ date         │         │ unit         │
│ address      │         │ opening_stock│         │ lead_time    │
│ created_at   │         │ received     │         │ min_stock    │
└──────────────┘         │ issued       │         │ created_at   │
                          │ closing_stock│         └──────────────┘
                          │ entered_by   │
                          │ created_at   │
                          └──────┬───────┘
                                 │
                                 │
                          ┌──────▼───────┐
                          │  Requisition │
                          ├──────────────┤
                          │ id            │
                          │ requisition_# │
             ┌────────────│ location_id   │
             │            │ requested_by  │
             │            │ department    │
             │            │ urgency       │
             │            │ status        │
             │            │ approved_by   │
             │            │ notes         │
             │            └──────┬────────┘
             │                   │ 1:N
             │                   ▼
             │          ┌─────────────────┐
             │          │ RequisitionItem │
             │          ├─────────────────┤
             │          │ id               │
             │          │ requisition_id   │
             │          │ item_id          │
             │          │ quantity_request │
             │          │ quantity_approved│
             │          │ notes            │
             └────────────────────────────┘
```

### 3.2 Entity Definitions

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Location** | Healthcare facility (hospital, clinic) | id, name, type, region, address |
| **Item** | Medical supply/medicine | id, name, category, unit, lead_time_days, min_stock |
| **InventoryTransaction** | Daily stock movement | id, location_id, item_id, date, opening_stock, received, issued, closing_stock |
| **Requisition** | Stock request | id, requisition_number, location_id, requested_by, department, urgency, status |
| **RequisitionItem** | Item in requisition | id, requisition_id, item_id, quantity_requested, quantity_approved |
| **ChatSession** | Conversation thread | id, user_id, title, created_at |
| **ChatMessage** | Individual message | id, session_id, role, content, created_at |
| **stock_health** | Derived view | location_id, item_id, current_stock, avg_daily_usage, days_remaining, health_status |

---

## 4. User Journeys

### 4.1 Vendor: Enter Inventory Data

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Vendor   │    │ DataEntry│    │ API      │    │Inventory│    │ Database│
│ Opens    │───▶│ Page     │───▶│ Endpoint │───▶│Service  │───▶│         │
│ DataEntry│    │ Fills    │    │ POST     │    │Process  │    │ Insert  │
└──────────┘    │ form     │    │ /bulk    │    │Business │    │ Transaction
                └──────────┘    └──────────┘    │ Rules   │    └──────────┘
                                      │         └──────────┘
                                      ▼
                               Success Response
```

**Steps:**
1. Vendor navigates to `/vendor`
2. Selects location, date
3. Enters item quantities (received/issued)
4. Submits bulk transaction
5. System calculates closing_stock = opening + received - issued
6. Saves to SQLite
7. Returns success confirmation

### 4.2 Staff: Create Requisition

```
┌──────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Staff    │    │ StaffRequis│    │ API      │    │Requisit-│    │ Database│
│ Opens    │───▶│ ition      │───▶│ Endpoint │───▶│ion      │───▶│         │
│ /staff   │    │ Page       │    │ POST     │    │Service  │    │ Insert  │
└──────────┘    │ Selects    │    │ /create  │    │Create   │    │ Req +   │
                │ items      │    │          │    │Requisit-│    │ Items   │
                │ quantity   │    └──────────┘    │ion      │    └──────────┘
                └─────────────┘                    └──────────┘
                                                      │
                                                      ▼
                                               Status: PENDING
```

**Steps:**
1. Staff navigates to `/staff`
2. Selects requesting location
3. Adds items and quantities
4. Sets urgency (LOW/NORMAL/HIGH/EMERGENCY)
5. Submits requisition
6. System creates requisition with PENDING status
7. Admin notified (future: email notification)

### 4.3 Admin: Approve Requisition

```
┌──────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Admin    │    │ Requisitions│   │ API      │    │Requisit-│    │ Database│
│ Opens    │───▶│ Page        │───▶│ Endpoint │───▶│ion      │───▶│         │
│ /admin/  │    │ Views       │    │ PUT      │    │Service  │    │ Update  │
│ requisi- │    │ pending     │    │ /approve │    │Approve  │    │ Status  │
│ tions    │    │ requisitions│    │          │    │         │    │         │
└──────────┘    └─────────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ▼
                                               Status: APPROVED
```

**Steps:**
1. Admin navigates to `/admin/requisitions`
2. Views pending requisitions
3. Reviews items and quantities
4. Clicks Approve or Reject
5. If reject, provides reason
6. System updates status
7. (Future) Staff notified, inventory auto-adjusted

### 4.4 Admin: View Analytics

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Admin    │    │Dashboard │    │ API      │    │Analytics│    │ Database│
│ Opens    │───▶│ Page     │───▶│ Endpoint │───▶│Service  │───▶│ Queries │
│ /admin/  │    │ Views    │    │ GET      │    │Aggregate│    │         │
│ dashboard│    │ charts   │    │ /stats   │    │Data     │    │         │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                       │                  │
                       │                  ▼
                       │           ┌──────────────┐
                       │           │ stock_health │
                       │           │ View         │
                       │           └──────────────┘
                       ▼
                 Display Charts
```

**Steps:**
1. Admin navigates to `/admin/dashboard`
2. System fetches analytics data
3. Service queries stock_health view
4. Aggregates by category, location, status
5. Returns chart data (pie, bar charts)
6. Frontend renders visualizations

### 4.5 Admin: AI Chat Query

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Admin    │    │ Chatbot  │    │ API      │    │AI Agent  │    │  LLM     │
│ Opens    │───▶│ Page     │───▶│ Endpoint │───▶│ Service  │───▶│ Groq    │
│ /admin/  │    │ Types    │    │ POST     │    │LangGraph │    │         │
│ chat     │    │ question │    │ /query   │    │Agent    │    │         │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘    └──────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────┐
                    │                               │               │
                    ▼                               ▼               ▼
              ┌──────────┐                  ┌──────────┐       ┌──────────┐
              │ SQLite   │                  │ ChromaDB │       │  Tool    │
              │ History  │                  │ Semantic │       │ Calling  │
              └──────────┘                  │ Memory   │       │ (SQL)    │
                                            └──────────┘       └────┬─────┘
                                                                          │
                                            ┌─────────────────────────────┘
                                            │
                                            ▼
                                      ┌──────────────┐
                                      │   Response   │
                                      │   Generated  │
                                      └──────┬───────┘
                                             │
                                             ▼
                                      Save to SQLite
                                             │
                                             ▼
                                      Save to ChromaDB
                                             │
                                             ▼
                                      Return to Frontend
```

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target | Notes |
|--------|--------|-------|
| **API Response Time** | < 500ms (p95) | Excluding AI chat |
| **AI Chat Response** | < 10s (p95) | Depends on LLM latency |
| **Page Load Time** | < 2s | Initial load |
| **Database Queries** | < 100ms (p95) | Simple queries |

### 5.2 Availability

| Metric | Target | Notes |
|--------|--------|-------|
| **Uptime** | 99.5% (prod) | Excluding maintenance |
| **Deployment Frequency** | On-demand | GitHub Actions |
| **Recovery Time Objective** | 1 hour | Database restore |
| **Recovery Point Objective** | 1 hour | Auto-backups |

### 5.3 Scalability

| Metric | Target | Notes |
|--------|--------|-------|
| **Concurrent Users** | 50 (initial) | Can scale vertically |
| **API Requests/minute** | 100 (initial) | Rate limited |
| **Database Connections** | 20 max | Pool size |

### 5.4 Security

| Requirement | Implementation |
|-------------|----------------|
| **Authentication** | JWT tokens (Phase 1) |
| **Authorization** | Role-based (Phase 1) |
| **HTTPS** | TLS 1.2+ (prod) |
| **Input Validation** | Pydantic schemas |
| **Rate Limiting** | 100 req/min (Phase 1) |

### 5.5 Data Retention

| Data Type | Retention | Notes |
|-----------|-----------|-------|
| **Transactions** | 7 years | Healthcare compliance |
| **Requisitions** | 7 years | Audit trail |
| **Chat History** | 1 year | Configurable |
| **Vector Memory** | Indefinite | Semantic search |
| **Logs** | 90 days | CloudWatch |

### 5.6 Compliance

| Requirement | Status |
|-------------|--------|
| **Input Validation** | ✅ Implemented |
| **Error Logging** | ✅ Implemented |
| **Audit Trail** | ⚠️ Partial (timestamps) |
| **Data Encryption** | ⚠️ At-rest (prod) |
| **Backup/Recovery** | ⚠️ Manual (dev) |

---

## 6. System Boundaries

### 6.1 What the System Does

- ✅ Inventory transaction management
- ✅ Requisition workflow (create → approve/reject)
- ✅ Stock health calculations
- ✅ AI-powered chat for inventory queries
- ✅ Analytics dashboard
- ✅ Voice input (speech-to-text)
- ✅ Cross-session semantic memory

### 6.2 What the System Does NOT Do (Yet)

- ❌ User authentication (Phase 1)
- ❌ Email notifications (Phase 6)
- ❌ Payment processing
- ❌ Multi-tenant isolation
- ❌ Advanced reporting
- ❌ Mobile app

---

## 7. Future Considerations

| Feature | Priority | Complexity |
|---------|----------|------------|
| JWT Authentication | Phase 1 | Medium |
| Role-based Access | Phase 1 | Medium |
| Redis Caching | Phase 4 | Low |
| PostgreSQL Migration | Phase 5 | Medium |
| WebSocket Real-time | Phase 6 | High |
| Email Notifications | Phase 6 | Medium |
