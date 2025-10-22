# app/routers/auth.py
"""
Authentication Router - Login, logout, dan token management

Router ini handle semua authentication operations di sistem billing.
Fokus pada JWT-based authentication dengan refresh token mechanism.

Authentication Flow:
1. Login -> dapat access token + refresh token
2. API calls -> pake access token (short-lived)
3. Token refresh -> pake refresh token (long-lived)
4. Logout -> blacklist refresh token

Security Features:
- JWT access tokens (15 menit lifetime)
- Refresh token rotation (7 hari lifetime)
- Token blacklisting untuk logout
- Rate limiting untuk brute force protection
- Session management (logout all devices)

Token Types:
- Access Token: API authentication (short-lived)
- Refresh Token: Token renewal (long-lived)
- Token blacklisting: Revocation mechanism

Endpoints:
- POST /auth/token - Login dan dapatkan tokens
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout dari current device
- POST /auth/logout-all - Logout dari semua devices
- GET /auth/password-requirements - Password policy

Integration Points:
- Rate limiting middleware
- Token service untuk refresh mechanism
- User model untuk authentication
- Permission system untuk authorization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
import logging
import uuid
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from ..database import get_db
from ..models.user import User as UserModel
from ..schemas.user import User as UserSchema
from ..schemas.token_blacklist import TokenRefreshRequest, TokenRefreshResponse
from ..auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_current_active_user,
    Token,
)
from ..config import settings
from ..services.token_service import get_token_service, TokenService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


# POST /auth/token - Login dan dapatkan access token
# Endpoint buat login user ke sistem dan dapetin JWT token
# Request body: form_data dengan username (email) dan password
# Response: access_token, refresh_token, token_type, expires_in
# Security:
# - Menggunakan OAuth2PasswordRequestForm untuk security
# - Password verification dengan hashing
# - JWT token dengan expiration time
# Token details:
# - Access token: 15 menit (configurable)
# - Refresh token: 7 hari
# - Token type: Bearer
# Validation: email dan password harus match di database
# Error handling: 401 kalo email/password salah
# Logging: log successful login untuk audit trail
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


# POST /auth/refresh - Refresh access token
# Buat dapatkan access token baru pake refresh token (tanpa login lagi)
# Request body: refresh_token yang masih valid
# Response: access_token baru, refresh_token baru, token_type, expires_in
# Security:
# - Validasi refresh token sebelum generate token baru
# - Refresh token rotation: refresh token lama di-blacklist, dapet baru
# - Auto-expired refresh token handling
# Token management:
# - Access token baru: 15 menit
# - Refresh token baru: 7 hari (extend dari yang lama)
# - Blacklist refresh token lama biar nggak bisa dipake lagi
# Use case: keep user logged in tanpa harus login ulang tiap 15 menit
# Error handling: 401 kalo refresh token invalid atau expired
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


# POST /auth/logout - Logout dari perangkat saat ini
# Buat logout user dan blacklist refresh token yang dipake
# Request body: refresh_token yang mau di-blacklist
# Response: success message
# Security:
# - Blacklist refresh token biar nggak bisa dipake lagi
# - Verify refresh token sebelum blacklist (validasi JWT)
# - Simpan alasan blacklist (User logout) untuk audit
# Token management:
# - Extract JTI (JWT ID) dari token untuk unique identification
# - Extract user ID dan expiration time dari token
# - Add ke token blacklist table
# Use case: logout normal user dari satu device
# Error handling: 401 kalo refresh token invalid atau expired
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


# POST /auth/logout-all - Logout dari semua perangkat
# Buat logout user dari semua device/session yang aktif
# Authentication: butuh access token yang valid (current user)
# Response: success message
# Security:
# - Revoke semua refresh token yang terkait user ini
# - Forced logout dari semua device yang sedang aktif
# - Gunakan current user dependency (authenticated user)
# Use case: security action (kalo curiga akun kena hack), reset session
# Token management:
# - Cari semua refresh token yang aktif untuk user ini
# - Blacklist semua token yang ditemukan
# - Include refresh token yang mungkin belum expired
# Performance: efficient query dengan filter by user_id
# Error handling: butuh authentication (401 kalo nggak login)
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


# GET /auth/password-requirements - Ambil requirement password
# Buat ngambil aturan password yang berlaku di sistem
# Response: password requirements (min length, uppercase, lowercase, dll)
# Use case: buat frontend validation form registration/change password
# Security features:
# - Minimum length requirement
# - Uppercase letter requirement
# - Lowercase letter requirement
# - Number requirement
# - Special character requirement
# - Custom pattern rules
# Implementation: import from main auth module
# Benefits: client-side validation tanpa hardcode rules di frontend
# Maintenance: centralized password policy management
@router.get("/password-requirements")
async def get_password_requirements():
    """
    Get password requirements untuk frontend validation.
    Returns security requirements for user guidance.
    """
    from .auth import get_password_requirements as get_req

    return {"status": "success", "data": get_req()}
