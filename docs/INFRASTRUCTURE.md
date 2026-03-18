# Infrastructure Document

**Project:** Smart Inventory Assistant  
**Date:** March 17, 2026

---

## 1. Cloud Provider

**Provider:** AWS (Amazon Web Services)  
**Reason:** Mature services, good Python ecosystem support, cost-effective for startup

---

## 2. Environment Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              INFRASTRUCTURE OVERVIEW                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│   │    Development  │    │   Staging       │    │   Production    │             │
│   │                 │    │                 │    │                 │             │
│   │  Local Machine  │    │  AWS EC2        │    │  AWS ECS Fargate│             │
│   │  (SQLite)       │    │  (PostgreSQL)   │    │  (PostgreSQL)   │             │
│   │                 │    │                 │    │  (ElastiCache)  │             │
│   │                 │    │                 │    │  (EFS)          │             │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Environment Details

### 3.1 Development Environment

| Component | Configuration |
|-----------|---------------|
| **Compute** | Local machine (developer laptop) |
| **Database** | SQLite (local file) |
| **Vector Store** | ChromaDB (local) |
| **Deployment** | Manual (`uvicorn`) |
| **Use Case** | Local development, debugging |

### 3.2 Staging Environment

| Component | Configuration |
|-----------|---------------|
| **Compute** | AWS EC2 t3.small |
| **Database** | AWS RDS PostgreSQL db.t3.micro |
| **Cache** | None (dev stage) |
| **Storage** | EBS gp3 (8GB) |
| **Domain** | staging.smart-inventory.internal |
| **Deployment** | GitHub Actions |

### 3.3 Production Environment

| Component | Configuration |
|-----------|---------------|
| **Compute** | AWS ECS Fargate (2 tasks, auto-scaling) |
| **Database** | AWS RDS PostgreSQL db.t3.medium |
| **Cache** | AWS ElastiCache Redis (cache.t3.micro) |
| **Storage** | AWS EFS (elastic file system) |
| **CDN** | CloudFront for static assets |
| **Load Balancer** | Application Load Balancer |
| **Domain** | api.smart-inventory.com |
| **SSL** | ACM Certificate Manager |
| **Deployment** | GitHub Actions (CI/CD) |

---

## 4. Networking

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCTION NETWORKING                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│                                    ┌──────────────────────┐                         │
│                                    │     Internet        │                         │
│                                    └──────────┬───────────┘                         │
│                                               │                                      │
│                                               ▼                                      │
│                                    ┌──────────────────────┐                         │
│                                    │   CloudFront CDN    │                         │
│                                    │  (Static Assets)   │                         │
│                                    └──────────┬───────────┘                         │
│                                               │                                      │
│                                               ▼                                      │
│                                    ┌──────────────────────┐                         │
│                                    │  Application Load   │                         │
│                                    │      Balancer       │                         │
│                                    │    (HTTPS/HTTPS)    │                         │
│                                    └──────────┬───────────┘                         │
│                                               │                                      │
│                    ┌───────────────────────────┼───────────────────────────┐        │
│                    │                           │                           │        │
│                    ▼                           ▼                           ▼        │
│           ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐ │
│           │    ECS Task     │      │    ECS Task     │      │   ECS Task       │ │
│           │    (Backend 1)  │      │    (Backend 2)  │      │   (Backend N)    │ │
│           │   FastAPI       │      │   FastAPI       │      │   FastAPI        │ │
│           └────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘ │
│                    │                          │                          │            │
│                    └──────────────────────────┼──────────────────────────┘            │
│                                               │                                      │
│                    ┌───────────────────────────┼───────────────────────────┐        │
│                    │                           │                           │        │
│                    ▼                           ▼                           ▼        │
│           ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐ │
│           │    RDS          │      │   ElastiCache    │      │       EFS         │ │
│           │  PostgreSQL     │      │     Redis        │      │   (ChromaDB)     │ │
│           │                 │      │   (Cache)       │      │   (Vector Store) │ │
│           └─────────────────┘      └──────────────────┘      └────────────────────┘ │
│                                                                                      │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                          VPC (10.0.0.0/16)                                   │  │
│   │  ┌─────────────────────────────────────────────────────────────────────────┐ │  │
│   │  │  Private Subnets: 10.0.1.0/24, 10.0.2.0/24 (2 AZ)                   │ │  │
│   │  │  Public Subnets: 10.0.101.0/24, 10.0.102.0/24 (for ALB)            │ │  │
│   │  └─────────────────────────────────────────────────────────────────────────┘ │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Service Specifications

### 5.1 Compute

| Environment | Service | Instance Type | Auto-Scaling |
|-------------|---------|---------------|---------------|
| Dev | Local | - | - |
| Staging | EC2 | t3.small | Manual |
| Prod | ECS Fargate | 0.5 vCPU / 1GB (min) | CPU 70% → scale |

### 5.2 Database

| Environment | Service | Type | Storage |
|-------------|---------|------|---------|
| Dev | SQLite | Local file | - |
| Staging | RDS PostgreSQL | db.t3.micro | 20GB gp3 |
| Prod | RDS PostgreSQL | db.t3.medium | 100GB gp3 |

### 5.3 Cache

| Environment | Service | Node Type |
|-------------|---------|-----------|
| Dev | None | - |
| Staging | None | - |
| Prod | ElastiCache Redis | cache.t3.micro |

### 5.4 Storage

| Environment | Service | Use Case |
|-------------|---------|----------|
| Dev | Local filesystem | ChromaDB |
| Staging | EBS | ChromaDB, logs |
| Prod | EFS | ChromaDB (vector store) |

---

## 6. CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD PIPELINE                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│   │  Push   │───▶│  Build  │───▶│  Test   │───▶│  Staging│───▶│  Prod   │        │
│   │  Code   │    │         │    │         │    │ Deploy  │    │ Deploy  │        │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘        │
│                                                                                      │
│   GitHub Actions:                                                                   │
│   1. Lint (flake8, ESLint)                                                         │
│   2. Type Check (mypy, TypeScript)                                                 │
│   3. Unit Tests (pytest, Vitest)                                                  │
│   4. Build Docker Image                                                            │
│   5. Push to ECR                                                                   │
│   6. Deploy to ECS Staging                                                        │
│   7. Manual Approval                                                               │
│   8. Deploy to ECS Production                                                     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Security

| Layer | Implementation |
|-------|----------------|
| **Network** | VPC with private subnets, security groups |
| **SSL/TLS** | ACM certificate, HTTPS only |
| **API** | Rate limiting (AWS WAF), API Keys |
| **Database** | IAM authentication, encryption at rest |
| **Secrets** | AWS Secrets Manager |
| **Backup** | RDS automated backups (7 days) |

---

## 8. Monitoring

| Metric | Tool |
|--------|------|
| **Logs** | CloudWatch Logs |
| **Metrics** | CloudWatch Metrics |
| **Alerts** | CloudWatch Alarms → SNS → Email |
| **Tracing** | LangSmith (AI), X-Ray (optional) |
| **Uptime** | CloudWatch Synthetics |

---

## 9. Cost Estimation (Monthly - Production)

| Service | Estimated Cost |
|---------|----------------|
| ECS Fargate | $25-50 |
| RDS PostgreSQL | $40-80 |
| ElastiCache Redis | $15-30 |
| EFS | $5-15 |
| CloudFront | $5-10 |
| Data Transfer | $5-10 |
| **Total** | **$95-195/month** |

---

## 10. Environment Variables by Stage

### Development (.env)
```env
DATABASE_PATH=../database/smart_inventory.db
ENVIRONMENT=development
GROQ_API_KEY=<key>
SARVAM_API_KEY=<key>
```

### Staging
```env
DATABASE_URL=postgresql://user:pass@staging-db:5432/inventory
ENVIRONMENT=staging
GROQ_API_KEY=<key>
SARVAM_API_KEY=<key>
REDIS_URL=redis://localhost:6379
```

### Production
```env
DATABASE_URL=postgresql://user:pass@prod-db.xxxx.us-east-1.rds.amazonaws.com:5432/inventory
ENVIRONMENT=production
GROQ_API_KEY=<secrets-manager>
SARVAM_API_KEY=<secrets-manager>
REDIS_URL=redis://prod-cache.xxxx.use1.cache.amazonaws.com:6379
```
