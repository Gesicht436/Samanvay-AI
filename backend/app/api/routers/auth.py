"""
Authentication and Role-Based Access Control (RBAC) API Router.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db_session, get_current_user
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from backend.app.models.tables import User
from backend.app.schemas.auth import (
    UserLogin,
    UserSignup,
    UserResponse,
    Token,
    SEED_USERS,
    DEFAULT_SEED_PASSWORD,
)
from backend.app.services.seeder import seed_users_if_empty

logger = logging.getLogger("samanvay.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user credentials and issue signed JWT bearer token",
)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db_session),
):
    """
    Authenticates a CPSE plant engineer, materials manager, CISF officer,
    or auditor and returns an access token embedding their tenant role and depot.
    """
    # Ensure seed users are available
    seed_users_if_empty(db)

    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact your CPSE administrator.",
        )

    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is pending approval by Super Admin.",
        )

    token_payload = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role,
        "cpse": user.cpse,
        "depot_id": user.depot_id,
        "full_name": user.full_name,
    }

    access_token = create_access_token(token_payload)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            cpse=user.cpse,
            depot_id=user.depot_id,
            is_active=user.is_active,
            is_approved=user.is_approved,
        ),
    )


@router.post(
    "/signup",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new CPSE officer or engineer and issue signed JWT bearer token",
)
def signup_user(
    signup_data: UserSignup,
    db: Session = Depends(get_db_session),
):
    """
    Registers an official CPSE plant engineer, stores manager, technical authority,
    or CISF officer and returns an immediate access token embedding their tenant role and depot.
    """
    # 1. Check if username already exists
    existing_user = db.query(User).filter(User.username == signup_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{signup_data.username}' is already registered.",
        )

    # 2. Check if email already exists
    existing_email = db.query(User).filter(User.email == signup_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{signup_data.email}' is already registered with another account.",
        )

    # 3. Create user
    hashed_pwd = get_password_hash(signup_data.password)
    user = User(
        username=signup_data.username.strip(),
        email=signup_data.email.strip().lower(),
        hashed_password=hashed_pwd,
        full_name=signup_data.full_name.strip(),
        role=signup_data.role.value if hasattr(signup_data.role, "value") else str(signup_data.role),
        cpse=signup_data.cpse.strip().upper(),
        depot_id=signup_data.depot_id.strip(),
        is_active=True,
        is_approved=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 4. Seal registration in Sovereign Audit Ledger
    try:
        from backend.app.services.audit_service import create_audit_entry
        create_audit_entry(
            db,
            {
                "actor": user.username,
                "actor_role": user.role,
                "action": "USER_REGISTRATION",
                "action_category": "ACCESS_CONTROL",
                "cpse": user.cpse,
                "depot": user.depot_id,
                "reference_id": f"USER-{user.id}",
                "payload": {
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "cpse": user.cpse,
                    "depot_id": user.depot_id,
                },
            },
        )
    except Exception as e:
        logger.warning(f"Failed to seal registration audit block: {e}")

    # 5. Issue JWT Token
    token_payload = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role,
        "cpse": user.cpse,
        "depot_id": user.depot_id,
        "full_name": user.full_name,
    }
    access_token = create_access_token(token_payload)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            cpse=user.cpse,
            depot_id=user.depot_id,
            is_active=user.is_active,
            is_approved=user.is_approved,
        ),
    )



@router.get(
    "/me",
    response_model=UserResponse,
    summary="Fetch current authenticated user profile and tenant claims",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the authenticated user details extracted from the Bearer JWT token.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        cpse=current_user.cpse,
        depot_id=current_user.depot_id,
        is_active=current_user.is_active,
        is_approved=current_user.is_approved,
    )


@router.get(
    "/seed-users",
    summary="List default seed persona accounts for evaluation and testing",
)
def get_seed_users():
    """
    Returns all pre-configured demo user accounts across OIL, IOCL, CISF, and MoPNG.
    """
    return {
        "default_password": DEFAULT_SEED_PASSWORD,
        "users": [user.model_dump() for user in SEED_USERS],
    }


@router.post(
    "/seed",
    summary="Idempotently ensure all default seed user accounts exist in DB",
)
def trigger_seed_users(
    db: Session = Depends(get_db_session),
):
    """Idempotently populates the database with seed accounts."""
    seed_users_if_empty(db)
    count = db.query(User).count()
    return {"status": "SUCCESS", "total_users": count}

@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users (Super Admin only)",
)
def get_all_users(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return db.query(User).all()

@router.post(
    "/users/{user_id}/approve",
    response_model=UserResponse,
    summary="Approve a pending user (Super Admin only)",
)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    db.commit()
    db.refresh(user)
    return user

@router.post(
    "/users/{user_id}/reject",
    summary="Reject and delete a pending user (Super Admin only)",
)
def reject_user(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"status": "User rejected and removed"}
