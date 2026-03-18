# API Contract Document

**Project:** Smart Inventory Assistant  
**Date:** March 17, 2026

---

## 1. API Overview

| Base URL | Environment |
|----------|-------------|
| `http://localhost:8000/api` | Development |
| `https://staging-api.smart-inventory.internal/api` | Staging |
| `https://api.smart-inventory.com/api` | Production |

---

## 2. Inventory APIs

### 2.1 Location Endpoints

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/inventory/locations` | GET | List all healthcare locations | Backend | All UIs |
| `/inventory/location/{id}/items` | GET | Get items with stock at location | Backend | Admin Inventory |

**Response - GET /inventory/locations**
```json
{
  "success": true,
  "data": [
    { "id": 1, "name": "City Hospital", "type": "HOSPITAL", "region": "North" }
  ]
}
```

---

### 2.2 Item Endpoints

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/inventory/items` | GET | List all inventory items | Backend | All UIs |

**Response - GET /inventory/items**
```json
{
  "success": true,
  "data": [
    { "id": 1, "name": "Paracetamol", "category": "Medicine", "unit": "tablets" }
  ]
}
```

---

### 2.3 Transaction Endpoints

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/inventory/transaction` | POST | Add single transaction | Backend | Vendor UI |
| `/inventory/bulk-transaction` | POST | Add multiple transactions | Backend | Vendor UI |
| `/inventory/stock/{location_id}/{item_id}` | GET | Get current stock level | Backend | Admin UI |
| `/inventory/reset-data` | POST | Reset database (dev only) | Backend | Admin UI |

**Request - POST /inventory/transaction**
```json
{
  "location_id": 1,
  "item_id": 1,
  "date": "2026-03-17",
  "received": 100,
  "issued": 50,
  "notes": "Daily stock update"
}
```

**Response - POST /inventory/transaction**
```json
{
  "success": true,
  "message": "Transaction added successfully",
  "data": {
    "id": 123,
    "opening_stock": 50,
    "received": 100,
    "issued": 50,
    "closing_stock": 100
  }
}
```

---

## 3. Requisition APIs

### 3.1 Requisition CRUD

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/requisition/create` | POST | Create new requisition | Backend | Staff UI |
| `/requisition/list` | GET | List requisitions (filterable) | Backend | Admin UI |
| `/requisition/{id}` | GET | Get requisition details | Backend | Admin UI |
| `/requisition/stats` | GET | Requisition statistics | Backend | Admin UI |

**Request - POST /requisition/create**
```json
{
  "location_id": 1,
  "requested_by": "John Doe",
  "department": "Emergency",
  "urgency": "HIGH",
  "items": [
    { "item_id": 1, "quantity_requested": 100 },
    { "item_id": 2, "quantity_requested": 50 }
  ],
  "notes": "Urgent requirement"
}
```

**Response - POST /requisition/create**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "requisition_number": "REQ-20260317-001",
    "status": "PENDING"
  }
}
```

---

### 3.2 Requisition Actions

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/requisition/{id}/approve` | PUT | Approve requisition | Backend | Admin UI |
| `/requisition/{id}/reject` | PUT | Reject requisition | Backend | Admin UI |
| `/requisition/{id}/cancel` | PUT | Cancel requisition | Backend | Admin/Staff |

**Request - PUT /requisition/{id}/approve**
```json
{
  "approved_by": "Admin User",
  "notes": "Approved for immediate processing"
}
```

**Request - PUT /requisition/{id}/reject**
```json
{
  "rejected_by": "Admin User",
  "rejection_reason": "Insufficient stock at source location"
}
```

---

## 4. Analytics APIs

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/analytics/heatmap` | GET | Stock level heatmap matrix | Backend | Dashboard |
| `/analytics/alerts` | GET | Critical/warning alerts | Backend | Dashboard |
| `/analytics/summary` | GET | Overall statistics | Backend | Dashboard |
| `/analytics/dashboard/stats` | GET | Chart data for dashboard | Backend | Dashboard |

**Response - GET /analytics/dashboard/stats**
```json
{
  "success": true,
  "data": {
    "category_distribution": [
      { "name": "Medicine", "value": 45 },
      { "name": "Supplies", "value": 30 }
    ],
    "low_stock_items": [
      { "name": "Paracetamol", "stock": 50, "min_stock": 100 }
    ],
    "status_distribution": [
      { "name": "CRITICAL", "value": 5 },
      { "name": "HEALTHY", "value": 70 }
    ]
  }
}
```

---

## 5. Chat APIs

### 5.1 Chat Operations

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/chat/query` | POST | Send question to AI | Backend | Chatbot UI |
| `/chat/history/{conversation_id}` | GET | Get conversation messages | Backend | Chatbot UI |
| `/chat/sessions` | GET | List all conversations | Backend | Chatbot UI |
| `/chat/suggestions` | GET | Get suggested questions | Backend | Chatbot UI |

**Request - POST /chat/query**
```json
{
  "question": "What items are critical in Mumbai?",
  "user_id": "admin",
  "conversation_id": null
}
```

**Response - POST /chat/query**
```json
{
  "success": true,
  "response": "There are 3 critical items in Mumbai...",
  "conversation_id": "conv_abc123",
  "suggested_actions": [
    { "type": "view", "label": "⚠️ View All Alerts", "action": "view_alerts" }
  ]
}
```

---

### 5.2 Speech-to-Text

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/chat/transcribe` | POST | Convert audio to text | Backend | Chatbot UI |

**Request - POST /chat/transcribe**
- Content-Type: `multipart/form-data`
- Body: `file` (audio file: wav, mp3, webm)

**Response - POST /chat/transcribe**
```json
{
  "success": true,
  "text": "What is the current stock of paracetamol?"
}
```

---

## 6. Health Check APIs

| Endpoint | Method | Purpose | Owner | Consumer |
|----------|--------|---------|-------|----------|
| `/` | GET | Root endpoint | Backend | All |
| `/health` | GET | Health check | Backend | Monitoring |

**Response - GET /health**
```json
{
  "status": "healthy",
  "database": "connected",
  "endpoints": ["/api/analytics/heatmap", "/api/chat/query", ...]
}
```

---

## 7. API Response Standards

### 7.1 Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}
```

### 7.2 Error Response
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_CODE"
}
```

### 7.3 Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE` | 409 | Resource already exists |
| `INVALID_STATE` | 400 | Operation not allowed in current state |
| `AUTHENTICATION_ERROR` | 401 | Invalid credentials |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `INTERNAL_ERROR` | 500 | Server error |

---

## 8. API Consumer Matrix

| API Group | Vendor UI | Staff UI | Admin UI | External |
|-----------|-----------|----------|----------|----------|
| `/inventory/locations` | ✅ Read | ✅ Read | ✅ Read | ❌ |
| `/inventory/items` | ✅ Read | ✅ Read | ✅ Read | ❌ |
| `/inventory/transaction` | ✅ Write | ❌ | ✅ Write | ❌ |
| `/requisition/create` | ❌ | ✅ Write | ✅ Write | ❌ |
| `/requisition/{id}/approve` | ❌ | ❌ | ✅ Write | ❌ |
| `/analytics/*` | ❌ | ❌ | ✅ Read | ❌ |
| `/chat/*` | ❌ | ❌ | ✅ Write | ❌ |

> **Note:** Currently all APIs are accessible to all UIs. Role-based access control (Phase 1) will enforce these boundaries.

---

## 9. Rate Limiting (Planned - Phase 1)

| Endpoint Group | Limit |
|----------------|-------|
| `/inventory/*` | 100 req/min |
| `/requisition/*` | 50 req/min |
| `/chat/query` | 10 req/min |
| `/chat/transcribe` | 5 req/min |

---

## 10. Versioning

| Version | Status | URL Prefix |
|---------|--------|------------|
| v1 | Current | `/api` |
| v2 | Planned | `/api/v2` |

---

## 11. Documentation

| Tool | URL | Description |
|------|-----|-------------|
| Swagger UI | `/docs` | Interactive API explorer |
| ReDoc | `/redoc` | Alternative documentation |
| OpenAPI JSON | `/openapi.json` | Raw OpenAPI spec |

---

## Summary Table

| Category | Endpoints | Owner | Consumer |
|----------|-----------|-------|----------|
| Health | 2 | Backend | All |
| Inventory | 7 | Backend | Vendor, Admin |
| Requisition | 7 | Backend | Staff, Admin |
| Analytics | 4 | Backend | Admin |
| Chat | 5 | Backend | Admin |
| **Total** | **25** | | |
