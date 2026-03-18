# Access Control Implementation Plan (Later)

Last updated: March 15, 2026

## Goal

Implement backend-enforced authentication and authorization so access is not only UI-based.

## Core Model

- Authentication: JWT-based login/session.
- Authorization: RBAC + scoped access.
- Scope: limit data/actions by `location_id` and optional `department`.

## Roles

- `super_admin`: full system control, manage admins and global settings.
- `admin`: manage users, inventory, requisitions in assigned scope.
- `staff`: create requisitions and view scoped inventory/requisition data.
- `vendor`: submit stock transactions for assigned locations.
- `viewer` (optional): read-only analytics/inventory.

## Permission Groups

- `users.manage` (create/update/deactivate users, assign roles/scopes)
- `inventory.read`
- `inventory.write`
- `inventory.reset`
- `requisition.create`
- `requisition.approve`
- `requisition.reject`
- `requisition.read_all`
- `analytics.read`
- `chat.use`

## Recommended Access Matrix

- `super_admin`: all permissions.
- `admin`: all except global-only controls reserved for `super_admin`.
- `staff`: `inventory.read`, `requisition.create`, `analytics.read` (scoped).
- `vendor`: `inventory.read`, `inventory.write` (scoped), no approvals.
- `viewer`: read-only permissions.

## Database Additions

- `users`:
  - `id`, `username`, `email`, `hashed_password`, `is_active`, `created_at`, `updated_at`
- `roles`:
  - `id`, `name` (unique)
- `permissions`:
  - `id`, `code` (unique), `description`
- `user_roles`:
  - `user_id`, `role_id`
- `role_permissions`:
  - `role_id`, `permission_id`
- `user_scopes`:
  - `user_id`, `location_id`, `department` (nullable)
- `permission_overrides` (optional):
  - `user_id`, `permission_id`, `effect` (`allow`/`deny`)
- `audit_logs`:
  - actor, target, action, payload, timestamp

## Backend Components to Add

- `backend/app/core/security.py`
  - password hashing/verification
  - JWT create/verify
- `backend/app/api/routes/auth.py`
  - register/login/me
- `backend/app/api/routes/users.py`
  - admin user provisioning and role/scope assignment
- `backend/app/core/permissions.py`
  - `require_permission(permission_code)`
  - scoped guards (`require_scope_location`)
- dependency injection updates in `core/dependencies.py`

## Route Protection Plan

- Protect all inventory/requisition/admin analytics endpoints with permission dependencies.
- Enforce scoped filtering in services/repositories:
  - users only see/manipulate data within allowed locations/departments.
- Keep `/health` and auth login/register public as needed.

## Admin Workflow

1. Admin creates a new user.
2. Admin assigns role(s).
3. Admin assigns scope (`location_id`, optional `department`).
4. User signs in and accesses only permitted endpoints/data.
5. Admin can update role/scope or deactivate user.
6. Every access-change action is written to `audit_logs`.

## Security Add-ons (same phase)

- Add rate limiting middleware.
- Add security headers middleware.
- Tighten CORS to known frontend origins only.

## Suggested Rollout Sequence

1. Create schema/tables for auth + RBAC.
2. Add JWT auth routes and password hashing.
3. Add permission dependencies and protect routes.
4. Add scoped filtering in query layer.
5. Add admin user-management APIs.
6. Add audit logging for permission changes.
7. Add tests for role and scope enforcement.

## Acceptance Criteria

- No protected endpoint is accessible without valid token.
- Role permissions are enforced by backend (not frontend only).
- Users cannot read/write outside assigned scope.
- Admin can create/update/deactivate users and assign roles/scopes.
- Audit logs capture all access-control changes.
