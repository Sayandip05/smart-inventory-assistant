from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_user_repo, get_current_user, require_admin
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_password,
)
from app.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from app.infrastructure.database.user_repo import UserRepository
from app.infrastructure.database.models import User
from app.api.schemas.auth_schemas import (
    UserCreate,
    UserResponse,
    LoginRequest,
    Token,
    RefreshTokenRequest,
    PasswordChangeRequest,
    RoleUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict)
def register(
    request: UserCreate,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    if request.role not in ["admin", "manager", "staff", "viewer"]:
        raise ValidationError(
            f"Invalid role: {request.role}. Must be admin, manager, staff, or viewer"
        )

    user = db.create(
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
        role=request.role,
    )

    return {
        "success": True,
        "message": f"User {user.username} created successfully",
        "data": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
        },
    }


@router.post("/login", response_model=dict)
def login(
    request: LoginRequest,
    db: Session = Depends(get_user_repo),
):
    user = db.get_by_username(request.username)
    if not user:
        raise AuthenticationError("Invalid username or password")

    if not verify_password(request.password, user.hashed_password):
        raise AuthenticationError("Invalid username or password")

    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    access_token = create_access_token(
        {"sub": user.id, "username": user.username, "role": user.role}
    )
    refresh_token = create_refresh_token({"sub": user.id, "username": user.username})

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
            },
        },
    }


@router.post("/refresh", response_model=dict)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_user_repo),
):
    payload = verify_refresh_token(request.refresh_token)
    user_id = payload.get("sub")

    user = db.get_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    access_token = create_access_token(
        {"sub": user.id, "username": user.username, "role": user.role}
    )
    refresh_token = create_refresh_token({"sub": user.id, "username": user.username})

    return {
        "success": True,
        "message": "Tokens refreshed",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    }


@router.get("/me", response_model=dict)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
        },
    }


@router.post("/change-password", response_model=dict)
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise AuthenticationError("Current password is incorrect")

    current_user.hashed_password = hash_password(request.new_password)
    db.update(current_user)

    return {
        "success": True,
        "message": "Password changed successfully",
    }


@router.get("/users", response_model=dict)
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    users = db.get_all(skip=skip, limit=limit)
    total = db.count()

    return {
        "success": True,
        "data": [
            {
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
            }
            for u in users
        ],
        "total": total,
    }


@router.put("/users/{user_id}/role", response_model=dict)
def update_user_role(
    user_id: int,
    request: RoleUpdate,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    if request.role not in ["admin", "manager", "staff", "viewer"]:
        raise ValidationError(f"Invalid role: {request.role}")

    user.role = request.role
    db.update(user)

    return {
        "success": True,
        "message": f"User role updated to {request.role}",
        "data": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.put("/users/{user_id}/activate", response_model=dict)
def activate_user(
    user_id: int,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    user.is_active = True
    db.update(user)

    return {
        "success": True,
        "message": f"User {user.username} activated",
    }


@router.put("/users/{user_id}/deactivate", response_model=dict)
def deactivate_user(
    user_id: int,
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

    return {
        "success": True,
        "message": f"User {user.username} deactivated",
    }


@router.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    db: Session = Depends(get_user_repo),
    current_user: User = Depends(require_admin),
):
    user = db.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)

    if user.id == current_user.id:
        raise ValidationError("Cannot delete your own account")

    db.delete(user_id)

    return {
        "success": True,
        "message": f"User {user.username} deleted",
    }
