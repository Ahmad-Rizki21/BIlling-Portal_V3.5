# app/auth.py

import uuid
from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .config import settings
from .database import get_db
from .models.role import Role
from .models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Membuat JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Membuat JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update(
        {"exp": expire, "iat": datetime.utcnow(), "type": "refresh", "jti": str(uuid.uuid4())}  # JWT ID for blacklisting
    )
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(email: str, password: str, db: AsyncSession) -> Union[User, None]:
    """Autentikasi user berdasarkan email dan password."""
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password):
        return None

    return user


def get_password_requirements():
    """Get password requirements untuk frontend validation."""
    return {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "no_whitespace": True,
    }


def validate_password_strength(password: str):
    """Validasi strength password sesuai requirements."""
    requirements = get_password_requirements()
    errors = []

    if len(password) < requirements["min_length"]:
        errors.append(f"Password harus minimal {requirements['min_length']} karakter")

    if not any(c.isupper() for c in password):
        errors.append("Password harus mengandung huruf besar")

    if not any(c.islower() for c in password):
        errors.append("Password harus mengandung huruf kecil")

    if not any(c.isdigit() for c in password):
        errors.append("Password harus mengandung angka")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Password harus mengandung karakter khusus")

    if any(c.isspace() for c in password):
        errors.append("Password tidak boleh mengandung spasi")

    return len(errors) == 0, errors


from typing import Optional

# Token data class untuk Pydantic models
class Token:
    def __init__(self, access_token: str, token_type: str, expires_in: int, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.refresh_token = refresh_token


def verify_access_token(token: str) -> dict:
    """Verifikasi JWT access token dan return payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise JWTError("Invalid token")


async def get_current_active_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Mengambil pengguna aktif berdasarkan token JWT untuk rute HTTP."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    query = select(User).where(User.id == int(user_id)).options(selectinload(User.role).selectinload(Role.permissions))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


def has_permission(required_permission: str):
    """
    Dependency yang memeriksa apakah user yang login
    memiliki permission yang dibutuhkan.
    """

    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        # Ambil semua nama permission yang dimiliki user
        user_permissions = {p.name for p in current_user.role.permissions}

        # Jika permission yang dibutuhkan tidak ada, tolak akses
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tidak memiliki hak akses untuk: '{required_permission}'",
            )

    return permission_checker


# --- FUNGSI BARU UNTUK OTENTIKASI WEBSOCKET ---
async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """
    Mendekode token JWT dan mengambil data user dari database.
    Didesain untuk digunakan di luar dependency injection standar (untuk WebSocket).
    """
    try:
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except (JWTError, ValueError, TypeError):
        # Return None instead of raising exception for WebSocket compatibility
        return None

    # Ambil user dari database
    try:
        query = select(User).where(User.id == int(user_id)).options(selectinload(User.role).selectinload(Role.permissions))
        user = (await db.execute(query)).scalar_one_or_none()
        return user
    except (ValueError, Exception):
        # Handle conversion errors and database errors
        return None
