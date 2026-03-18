# What Will Be Implemented

Last updated from code scan: March 15, 2026

## Priority Order (Execution Plan)

### Phase 1: Production-Safe Access and Security

1. Module 4 - Authentication and Authorization
- Add user model, login endpoint, JWT issuance, token validation dependency.
- Enforce role checks on protected inventory/requisition/admin endpoints.

2. Module 15 - Backend Security
- Add request rate limiting.
- Add security response headers.
- Add backend-level access control to remove UI-only trust.

### Phase 2: Testability and Quality Gate

3. Module 19 - Testing and Code Quality
- Add pytest + FastAPI TestClient test suite.
- Add dependency overrides and DB fixtures.
- Cover route + service layer behavior and failure paths.

### Phase 3: Runtime Reliability

4. Module 14 - Graceful Shutdown and Lifespan
- Add startup/shutdown lifecycle hooks.
- Close/dispose DB and memory resources cleanly.

5. Module 10 - Task Queues (or FastAPI background tasks as first step)
- Move non-critical work (memory indexing/notifications) out of request path.

6. Module 18 - Concurrency and Parallelism
- Convert blocking routes/services where safe.
- Remove shared mutable global patterns that can break under concurrent load.

### Phase 4: Performance and Scale Baseline

7. Module 16 - Scaling and Performance Part A
- Tighten query performance strategy (indexes, query plans, slow query logs).
- Formalize DB engine pool settings for target runtime.

8. Module 9 - Caching (Redis)
- Add cache strategy for read-heavy analytics and reference data.
- Add invalidation on write paths.

### Phase 5: Delivery and Deployability

9. Module 27 - DevOps and Containerization
- Replace placeholder Dockerfile with production image.
- Create meaningful docker-compose services and health checks.
- Add real CI pipeline in `cicd.yaml`.

10. Module 17 - Scaling and Performance Part B
- Define multi-worker process model and stateless deployment strategy.

### Phase 6: Platform Features (After Core Stability)

11. Module 25 - API Documentation hardening (currently partial)
- Add explicit `response_model` coverage and examples.

12. Module 20 - Object Storage and Large Files
13. Module 21 - Real-Time Systems
14. Module 22 - Webhooks
15. Module 24 - Transactional Emails and async notifications
16. Module 23 - Advanced Search
17. Module 26 - 12-Factor completion (runtime and deploy parity hardening)

## Immediate Next 4 Modules (Recommended)

1. Module 4 (Auth)
2. Module 15 (Security)
3. Module 19 (Testing)
4. Module 27 (DevOps/Containerization)
