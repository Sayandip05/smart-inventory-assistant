import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_user_repo, get_current_user, require_admin
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.core.security import (
    authenticate_user,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_password,
)
from app.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from app.infrastructure.database.user_repo import UserRepository
from app.infrastructure.database.models import User
from app.application.audit_service import AuditService
from app.api.schemas.auth_schemas import (
    UserCreate,
    UserResponse,
    UserProfileUpdate,
    AdminPasswordReset,
    LoginRequest,
    Token,
    RefreshTokenRequest,
    PasswordChangeRequest,
    RoleUpdate,
)

logger = logging.getLogger("smart_inventory.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Constants ──────────────────────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS = settings.MAX_LOGIN_ATTEMPTS
LOCKOUT_DURATION_MINUTES = settings.LOCKOUT_DURATION_MINUTES


# ── Helpers ────────────────────────────────────────────────────────────────

def _user_dict(user: User) -> dict:
    """Standard user data payload reused across endpoints."""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login_at": str(user.last_login_at) if user.last_login_at else None,
    }


def _get_client_ip(request: Request) -> str:
    """Extract client IP for audit logging."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── POST /register ─────────────────────────────────────────────────────────

@router.post("/register", response_model=dict)
@limiter.limit("3/minute")
def register(
    request_body: UserCreate,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    if request_body.role not in ["admin", "manager", "staff", "viewer"]:
        raise ValidationError(
            f"Invalid role: {request_body.role}. Must be admin, manager, staff, or viewer"
        )

    user = db.create(
        email=request_body.email,
        username=request_body.username,
        password=request_body.password,
        full_name=request_body.full_name,
        role=request_body.role,
    )

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="USER_CREATED",
        resource_type="user",
        resource_id=str(user.id),
        user_id=current_user.id,
        details={"new_user": user.username, "role": user.role},
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": f"User {user.username} created successfully",
        "data": _user_dict(user),
    }


# ── POST /login ────────────────────────────────────────────────────────────

@router.post("/login", response_model=dict)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(
    request_body: LoginRequest,
    request: Request,
    db: Session = Depends(get_user_repo),
):
    user = db.get_by_username(request_body.username)
    # NOTE: we do NOT raise early if user is None — that would leak username
    # existence via timing. authenticate_user() runs a dummy hash in that case.

    # Check account lockout (only if user exists)
    if user and user.locked_until:
        now = datetime.now(timezone.utc)
        if now < user.locked_until:
            remaining = int((user.locked_until - now).total_seconds() // 60) + 1
            raise AuthenticationError(
                f"Account is locked. Try again in {remaining} minutes."
            )
        else:
            # Lock period expired, reset
            db.reset_login_attempts(user)

    # ── Verify password (timing-safe via authenticate_user) ─────────────
    # authenticate_user always runs a dummy hash if user is None,
    # preventing username enumeration via response timing differences.
    if not authenticate_user(user, request_body.password):
        if user is not None:
            db.increment_login_attempts(user)
            attempts_left = MAX_LOGIN_ATTEMPTS - (user.login_attempts or 0)

            if attempts_left <= 0:
                # Lock the account
                lock_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                db.lock_user(user, lock_until)

                audit = AuditService(db.db)
                audit.log(
                    username=user.username,
                    action="ACCOUNT_LOCKED",
                    resource_type="user",
                    resource_id=str(user.id),
                    details={"reason": "max_login_attempts_exceeded"},
                    ip_address=_get_client_ip(request),
                )

                raise AuthenticationError(
                    f"Account locked for {LOCKOUT_DURATION_MINUTES} minutes due to too many failed attempts."
                )

        raise AuthenticationError("Invalid username or password")

    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    # Successful login — record it and reset attempts
    db.record_login(user)

    access_token = create_access_token(
        {"sub": user.id, "username": user.username, "role": user.role, "org_id": user.org_id}
    )
    refresh_token = create_refresh_token({"sub": user.id, "username": user.username})

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=user.username,
        action="LOGIN_SUCCESS",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": _user_dict(user),
        },
    }


# ── POST /logout ───────────────────────────────────────────────────────────

@router.post("/logout", response_model=dict)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_user_repo),
):
    """Blacklist the current access token (and optionally refresh token)."""
    from app.infrastructure.cache.token_blacklist import (
        blacklist_token,
        blacklist_refresh_token,
    )

    # Extract the access token from the Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        blacklist_token(access_token)

    # Audit log — reuse the injected db session, no extra connection
    try:
        audit = AuditService(db)
        audit.log(
            username=current_user.username,
            action="LOGOUT",
            resource_type="user",
            resource_id=str(current_user.id),
            user_id=current_user.id,
            ip_address=_get_client_ip(request),
        )
    except Exception:
        pass

    return {"success": True, "message": "Logged out successfully"}


# ── POST /refresh ──────────────────────────────────────────────────────────

@router.post("/refresh", response_model=dict)
@limiter.limit("10/minute")
def refresh_token(
    request: Request,
    db: Session = Depends(get_user_repo),
):
    """
    Refresh access token. Implements token rotation:
    the old refresh token is blacklisted after use (one-time use only).
    
    Accepts refresh_token in request body.
    """
    from app.infrastructure.cache.token_blacklist import (
        blacklist_refresh_token as bl_refresh,
        is_token_blacklisted,
    )
    import json
    
    # Parse request body manually to get refresh_token
    try:
        body = json.loads(request._body.decode()) if hasattr(request, '_body') and request._body else {}
    except:
        body = {}
    
    refresh_token_str = body.get('refresh_token') if body else None
    
    if not refresh_token_str:
        raise AuthenticationError("refresh_token is required")

    # Reject if the refresh token was already used (rotation replay attack)
    if is_token_blacklisted(refresh_token_str):
        raise AuthenticationError("Refresh token has already been used or revoked")

    payload = verify_refresh_token(refresh_token_str)
    user_id = payload.get("sub")

    user = db.get_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    # ── Token rotation: blacklist the old refresh token ────────────────
    bl_refresh(refresh_token_str)

    access_token = create_access_token(
        {"sub": user.id, "username": user.username, "role": user.role, "org_id": user.org_id}
    )
    new_refresh_token = create_refresh_token({"sub": user.id, "username": user.username})

    return {
        "success": True,
        "message": "Tokens refreshed (old refresh token revoked)",
        "data": {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        },
    }


# ── GET /me ────────────────────────────────────────────────────────────────

@router.get("/me", response_model=dict)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": _user_dict(current_user),
    }


# ── PATCH /me ──────────────────────────────────────────────────────────────

@router.patch("/me", response_model=dict)
def update_my_profile(
    request_body: UserProfileUpdate,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(get_current_user),
):
    changes = {}
    if request_body.email is not None:
        # Check for duplicate email
        existing = db.get_by_email(str(request_body.email))
        if existing and existing.id != current_user.id:
            raise ValidationError("Email already in use by another account")
        current_user.email = str(request_body.email)
        changes["email"] = str(request_body.email)

    if request_body.full_name is not None:
        current_user.full_name = request_body.full_name
        changes["full_name"] = request_body.full_name

    if not changes:
        raise ValidationError("No fields provided to update")

    db.update(current_user)

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="PROFILE_UPDATED",
        resource_type="user",
        resource_id=str(current_user.id),
        user_id=current_user.id,
        details=changes,
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": _user_dict(current_user),
    }


# ── POST /change-password ─────────────────────────────────────────────────

@router.post("/change-password", response_model=dict)
def change_password(
    request_body: PasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(request_body.current_password, current_user.hashed_password):
        raise AuthenticationError("Current password is incorrect")

    current_user.hashed_password = hash_password(request_body.new_password)
    db.update(current_user)

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="PASSWORD_CHANGED",
        resource_type="user",
        resource_id=str(current_user.id),
        user_id=current_user.id,
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": "Password changed successfully",
    }


# ── GET /users ─────────────────────────────────────────────────────────────

@router.get("/users", response_model=dict)
def list_users(
    skip: int = 0,
    limit: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    if role and role not in ["admin", "manager", "staff", "viewer"]:
        raise ValidationError(f"Invalid role filter: {role}")
    if limit > 100:
        limit = 100  # Cap to prevent abuse

    users = db.get_all_filtered(role=role, is_active=is_active, skip=skip, limit=limit)
    total = db.count_filtered(role=role, is_active=is_active)

    return {
        "success": True,
        "data": [_user_dict(u) for u in users],
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total,
        },
        "filters": {"role": role, "is_active": is_active},
    }


# ── GET /users/{user_id} ──────────────────────────────────────────────────

@router.get("/users/{user_id}", response_model=dict)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    return {
        "success": True,
        "data": _user_dict(user),
    }


# ── PUT /users/{user_id}/role ─────────────────────────────────────────────

@router.put("/users/{user_id}/role", response_model=dict)
def update_user_role(
    user_id: int,
    request_body: RoleUpdate,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    if request_body.role not in ["admin", "manager", "staff", "viewer"]:
        raise ValidationError(f"Invalid role: {request_body.role}")

    old_role = user.role
    user.role = request_body.role
    db.update(user)

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="ROLE_CHANGED",
        resource_type="user",
        resource_id=str(user.id),
        user_id=current_user.id,
        details={"target_user": user.username, "old_role": old_role, "new_role": user.role},
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": f"User role updated to {request_body.role}",
        "data": _user_dict(user),
    }


# ── PUT /users/{user_id}/activate ─────────────────────────────────────────

@router.put("/users/{user_id}/activate", response_model=dict)
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    user.is_active = True
    db.update(user)

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="USER_ACTIVATED",
        resource_type="user",
        resource_id=str(user.id),
        user_id=current_user.id,
        details={"target_user": user.username},
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": f"User {user.username} activated",
    }


# ── PUT /users/{user_id}/deactivate ───────────────────────────────────────

@router.put("/users/{user_id}/deactivate", response_model=dict)
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    if user.id == current_user.id:
        raise ValidationError("Cannot deactivate your own account")

    user.is_active = False
    db.update(user)

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="USER_DEACTIVATED",
        resource_type="user",
        resource_id=str(user.id),
        user_id=current_user.id,
        details={"target_user": user.username},
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": f"User {user.username} deactivated",
    }


# ── POST /users/{user_id}/reset-password ──────────────────────────────────

@router.post("/users/{user_id}/reset-password", response_model=dict)
def admin_reset_password(
    user_id: int,
    request_body: AdminPasswordReset,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    user.hashed_password = hash_password(request_body.new_password)
    # Also unlock and reset attempts if they were locked
    user.login_attempts = 0
    user.locked_until = None
    db.update(user)

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="PASSWORD_RESET_BY_ADMIN",
        resource_type="user",
        resource_id=str(user.id),
        user_id=current_user.id,
        details={"target_user": user.username},
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": f"Password for {user.username} has been reset",
    }


# ── DELETE /users/{user_id} ───────────────────────────────────────────────

@router.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    if user.id == current_user.id:
        raise ValidationError("Cannot delete your own account")

    deleted_username = user.username
    db.delete(user_id)

    # Audit log
    audit = AuditService(db.db)
    audit.log(
        username=current_user.username,
        action="USER_DELETED",
        resource_type="user",
        resource_id=str(user_id),
        user_id=current_user.id,
        details={"deleted_user": deleted_username},
        ip_address=_get_client_ip(request),
    )

    return {
        "success": True,
        "message": f"User {deleted_username} deleted",
    }
