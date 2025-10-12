# app/routers/auth.py

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..auth import (
    Token,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    get_password_hash,
)
from ..config import settings
from ..database import get_db
from ..models.user import User as UserModel
from ..schemas.token_blacklist import TokenRefreshRequest, TokenRefreshResponse
from ..schemas.user import User as UserSchema
from ..services.token_service import TokenService, get_token_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Endpoint untuk login dan mendapatkan access token.
    """
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buat access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email}, expires_delta=access_token_expires)

    # Buat refresh token
    refresh_token_expires = timedelta(days=7)
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    logger.info(f"User {user.email} logged in successfully")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(
    refresh_request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    token_service: TokenService = Depends(get_token_service),
):
    """
    Endpoint untuk merefresh access token menggunakan refresh token.
    """
    result = await token_service.refresh_access_token(db, refresh_request.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau telah dicabut",
        )

    new_access_token, new_refresh_token, expires_in = result
    return TokenRefreshResponse(
        access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer", expires_in=expires_in
    )


@router.post("/logout")
async def logout(
    refresh_request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    token_service: TokenService = Depends(get_token_service),
):
    """Blacklist refresh token saat logout."""
    # Verifikasi refresh token
    try:
        payload = jwt.decode(refresh_request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token kadaluarsa")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token tidak valid")

    # Ekstrak informasi dari token
    jti = payload.get("jti")
    user_id = payload.get("sub")
    exp = datetime.fromtimestamp(payload.get("exp", 0))

    if not jti or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token tidak valid")

    await token_service.blacklist_token(db, jti, int(user_id), "refresh", exp, "User logout")
    return {"message": "Logout berhasil"}


@router.post("/logout-all")
async def logout_all(
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    token_service: TokenService = Depends(get_token_service),
):
    """
    Endpoint untuk logout dari semua perangkat.
    """
    await token_service.revoke_all_user_tokens(db, current_user.id)
    return {"message": "Logout dari semua perangkat berhasil"}


@router.get("/password-requirements")
async def get_password_requirements():
    """
    Get password requirements untuk frontend validation.
    Returns security requirements for user guidance.
    """
    from .auth import get_password_requirements as get_req

    return {"status": "success", "data": get_req()}
