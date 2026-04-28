# LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
# Copyright (C) 2025 LogiSwarm Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import (
    TokenPayload,
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.db.session import get_db_session
from app.db.user_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(BaseModel):
    """Response for successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """User information in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: str
    display_name: str | None
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    """Request body for creating a new user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = None


class UserUpdate(BaseModel):
    """Request body for updating a user."""

    display_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class AuthEnvelope(BaseModel):
    """Standard API envelope for auth responses."""

    model_config = ConfigDict(extra="allow")

    data: Any
    error: str | None = None
    meta: dict[str, Any] | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> TokenPayload | None:
    """Extract and validate the current user from the Authorization header."""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        return None

    return TokenPayload(payload)


async def require_user(
    user: TokenPayload | None = Depends(get_current_user),
) -> TokenPayload:
    """Require a valid authenticated user."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_operator(
    user: TokenPayload = Depends(require_user),
) -> TokenPayload:
    """Require an operator or admin role."""
    if not user.is_operator:
        raise HTTPException(status_code=403, detail="Operator or admin role required")
    return user


async def require_admin(
    user: TokenPayload = Depends(require_user),
) -> TokenPayload:
    """Require admin role."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


@router.post("/login", response_model=AuthEnvelope)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthEnvelope:
    """Authenticate user and return JWT token."""
    stmt = select(User).where(User.email == payload.email.lower())
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.last_login = datetime.now(UTC)
    await session.commit()

    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )

    return AuthEnvelope(
        data=LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=24 * 3600,
            user=UserResponse.model_validate(user),
        ),
        error=None,
        meta=None,
    )


@router.post("/register", response_model=AuthEnvelope)
async def register(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload | None = Depends(get_current_user),
) -> AuthEnvelope:
    """Register a new user. First user becomes admin."""
    existing = await session.execute(
        select(User).where(User.email == payload.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user_count = await session.execute(select(func.count()).select_from(User))
    is_first_user = user_count.scalar() == 0

    role = "admin" if is_first_user else "viewer"

    if current_user is not None and current_user.is_admin:
        role = "viewer"

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=role,
        display_name=payload.display_name,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info(f"Registered new user: {user.email} with role {user.role}")

    return AuthEnvelope(
        data=UserResponse.model_validate(user),
        error=None,
        meta={"first_user": is_first_user},
    )


@router.get("/me", response_model=AuthEnvelope)
async def get_current_user_info(
    user: TokenPayload = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
) -> AuthEnvelope:
    """Get current authenticated user information."""
    user_uuid = UUID(user.user_id)
    db_user = await session.get(User, user_uuid)

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return AuthEnvelope(
        data=UserResponse.model_validate(db_user),
        error=None,
        meta=None,
    )


@router.get("/users", response_model=AuthEnvelope)
async def list_users(
    role: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin: TokenPayload = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AuthEnvelope:
    """List all users. Admin only."""
    stmt = select(User)

    if role:
        stmt = stmt.where(User.role == role)

    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    users = result.scalars().all()

    return AuthEnvelope(
        data=[UserResponse.model_validate(u) for u in users],
        error=None,
        meta={"total": len(users), "limit": limit, "offset": offset},
    )


@router.put("/users/{user_id}", response_model=AuthEnvelope)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    admin: TokenPayload = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AuthEnvelope:
    """Update a user's role or status. Admin only."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.display_name is not None:
        user.display_name = payload.display_name

    if payload.role is not None:
        valid_roles = {"viewer", "operator", "admin"}
        if payload.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
            )
        user.role = payload.role

    if payload.is_active is not None:
        user.is_active = payload.is_active

    await session.commit()
    await session.refresh(user)

    return AuthEnvelope(
        data=UserResponse.model_validate(user),
        error=None,
        meta={"updated": True},
    )


@router.delete("/users/{user_id}", response_model=AuthEnvelope)
async def delete_user(
    user_id: UUID,
    admin: TokenPayload = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AuthEnvelope:
    """Delete a user. Admin only."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if str(user_id) == admin.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await session.delete(user)
    await session.commit()

    return AuthEnvelope(
        data={"deleted": True},
        error=None,
        meta=None,
    )
