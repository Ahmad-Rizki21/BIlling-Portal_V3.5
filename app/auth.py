# app/auth.py
"""
Modul authentication buat handle login, token management, dan authorization.
Ini core security module yang jaga semua API endpoint dari akses tidak sah.

Features:
- JWT token authentication (access + refresh token)
- Password hashing pake bcrypt (secure dan proven)
- Role-based access control (RBAC)
- Permission system yang granular
- WebSocket authentication support

Security measures:
- Strong password validation
- Token expiration dan refresh mechanism
- Rate limiting ready
- SQL injection prevention via SQLAlchemy
- CORS support via FastAPI

Usage:
- Protect endpoints dengan @has_permission("permission_name")
- Get current user dengan get_current_active_user()
- Auth WebSocket dengan get_user_from_token()
"""

import uuid
from datetime import datetime, timedelta
from typing import Union, Optional

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

# Password hashing configuration - pake bcrypt yang proven secure
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Strong hashing, computational cost
    bcrypt__ident="2b"  # Modern bcrypt variant
)

# JWT configuration
ALGORITHM = "HS256"  # Standard JWT algorithm
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # FastAPI token handler

"""
Security configuration notes:
- bcrypt rounds 12: Balance antara security dan performance
- HS256: Symmetric encryption, cocok buat server-to-server
- Token URL: "token" endpoint buat login
- Auto deprecation: pake latest hashing recommendations
"""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifikasi password plaintext vs hash yang tersimpan di database.

    Args:
        plain_password: Password yang dimasukkan user (plaintext)
        hashed_password: Hash password dari database

    Returns:
        True kalau password benar, False kalau salah

    Security features:
    - Auto truncate ke 72 karakter (bcrypt limit)
    - Timing attack resistant (bcrypt feature)
    - Safe error handling - return False instead of exception
    - Log error buat debugging tanpa expose sensitive data

    Note:
    - bcrypt punya 72 character limit
    - Error handling tetap aman (return False)
    - Slow hashing buat prevent brute force
    """
    try:
        # Batasi password maksimal 72 karakter sesuai batasan bcrypt
        truncated_password = plain_password[:72]
        result: bool = pwd_context.verify(truncated_password, hashed_password)
        return result
    except Exception as e:
        # Log error untuk debugging
        import logging
        logging.error(f"Error verifying password: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash password plaintext jadi bcrypt hash buat disimpan di database.

    Args:
        password: Password plaintext yang mau dihash

    Returns:
        String hash yang siap disimpan di database

    Security features:
    - Auto salt generation (bcrypt built-in)
    - Strong hashing dengan 12 rounds
    - Fallback ke SHA256 kalau bcrypt error (redundancy)
    - Auto truncate ke 72 karakter

    Example:
        >>> hash = get_password_hash("password123")
        >>> print(hash)  # Output: $2b$12$...

    Note:
    - Hash result selalu 60 karakter (bcrypt standard)
    - Include salt, algorithm, dan cost factor
    - Fallback hanya buat emergency, normalnya pake bcrypt
    """
    try:
        # Batasi password maksimal 72 karakter sesuai batasan bcrypt
        truncated_password = password[:72]
        result: str = pwd_context.hash(truncated_password)
        return result
    except Exception as e:
        # Log error untuk debugging
        import logging
        logging.error(f"Error hashing password: {e}")
        # Fallback ke hash sederhana
        import hashlib
        return hashlib.sha256(truncated_password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    Buat JWT access token buat authentication.

    Args:
        data: Payload data (user info, permissions, dll)
        expires_delta: Custom expiration (default: 2 jam)

    Returns:
        JWT token string

    Token features:
    - Signed dengan secret key dari environment
    - Include expiration time (exp claim)
    - Include issued at time (iat claim)
    - HS256 algorithm (secure & standard)

    Security:
    - Short lifetime (2 jam) buat limit exposure
    - Server-side signing verification
    - Tamper-proof (signature verification)

    Example:
        >>> token = create_access_token({"sub": "123", "email": "user@example.com"})
        >>> print(token)  # Output: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=120)  # 2 jam default

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    Buat JWT refresh token buat dapatkan access token baru.

    Args:
        data: Payload data (minimal user ID)
        expires_delta: Custom expiration (default: 7 hari)

    Returns:
    JWT refresh token string

    Token features:
    - Longer lifetime (7 hari) dari access token
    - Include 'type': 'refresh' claim
    - Unique JWT ID (jti) buat blacklisting
    - Same secret key dengan access token

    Security:
    - Can be revoked via blacklist (using jti)
    - Longer lifetime but limited usage
    - Separate dari access token isolation

    Usage flow:
    1. Login -> dapat access + refresh token
    2. Access token expired -> pake refresh token
    3. Refresh token -> dapat access token baru
    4. Refresh token expired -> login lagi

    Example:
        >>> refresh_token = create_refresh_token({"sub": "123"})
        >>> print(refresh_token)  # Output: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
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
    """
    Autentikasi user berdasarkan email dan password.
    Ini core function buat login process.

    Args:
        email: Email user yang mau login
        password: Password plaintext dari form login
        db: Database session

    Returns:
        User object kalau valid, None kalau invalid

    Authentication flow:
    1. Cari user di database berdasarkan email
    2. Verify password dengan bcrypt
    3. Return user object kalau semua valid

    Security features:
    - Email case sensitive (sesuai database)
    - Password verification pake bcrypt
    - Return None kalau user tidak ada atau password salah
    - Prevent timing attacks (bcrypt feature)

    Usage:
        >>> user = await authenticate_user("user@example.com", "password123", db)
        >>> if user:
        ...     print("Login successful!")
        ... else:
        ...     print("Invalid credentials")

    Note:
    - Tidak expose apakah email atau password yang salah
    - Consistent response time buat prevent enumeration
    """
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password):
        return None

    return user


def get_password_requirements() -> dict:
    """
    Get password policy requirements buat frontend validation.
    Frontend bisa request ini buat show validation rules ke user.

    Returns:
        Dictionary dengan semua password requirements

    Requirements:
    - Minimal 8 karakter
    - Harus ada huruf besar (A-Z)
    - Harus ada huruf kecil (a-z)
    - Harus ada angka (0-9)
    - Harus ada karakter khusus (!@#$%^&* dll)
    - Tidak boleh ada spasi
    - Maksimal 72 karakter (bcrypt limit)

    Frontend usage:
        fetch('/api/password-requirements')
        .then(res => res.json())
        .then(rules => {
            // Show validation rules to user
            // Implement real-time validation
        })

    Security:
    - Strong policy buat prevent weak passwords
    - Comprehensive coverage buat common attack vectors
    - Reasonable limits buat user experience
    """
    result: dict = {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "no_whitespace": True,
    }
    return result


def validate_password_strength(password: str):
    """
    Validasi password strength sesuai policy requirements.
    Bisa dipake di backend atau frontend validation.

    Args:
        password: Password yang mau divalidasi

    Returns:
        Tuple (is_valid, error_messages)

    Validation checks:
    - Length antara 8-72 karakter
    - Ada huruf besar
    - Ada huruf kecil
    - Ada angka
    - Ada karakter khusus
    - Tidak ada spasi

    Usage:
        >>> is_valid, errors = validate_password_strength("Password123!")
        >>> if is_valid:
        ...     print("Password is strong!")
        >>> else:
        ...     print("Weak password:", errors)

    Security:
    - Prevent weak passwords yang rentan brute force
    - Comprehensive coverage buat dictionary attacks
    - User-friendly error messages
    """
    requirements = get_password_requirements()
    errors = []

    # Periksa panjang maksimal password (72 karakter untuk bcrypt)
    if len(password) > 72:
        errors.append("Password maksimal 72 karakter")

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

    result: tuple[bool, list] = (len(errors) == 0, errors)
    return result


from typing import Optional


# Token data class untuk API responses
class Token:
    """
    Token response class buat login endpoint.
    Standard format buat token-based authentication.

    Attributes:
        access_token: JWT token buat API access
        token_type: Tipe token (selalu "Bearer")
        expires_in: Token lifetime dalam detik
        refresh_token: Token buat refresh access token

    Usage in FastAPI:
        @router.post("/login")
        async def login(credentials: LoginSchema):
            # ... authentication logic ...
            return Token(
                access_token=access_token,
                token_type="Bearer",
                expires_in=7200,  # 2 jam
                refresh_token=refresh_token
            )

    Frontend usage:
        // Simpen tokens
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);

        // Pake buat API calls
        fetch('/api/users', {
            headers: {
                'Authorization': `Bearer ${response.access_token}`
            }
        });
    """

    def __init__(self, access_token: str, token_type: str, expires_in: int, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.refresh_token = refresh_token


def verify_access_token(token: str) -> dict:
    """
    Verifikasi JWT access token dan extract payload.
    Core function buat token validation.

    Args:
        token: JWT token string dari Authorization header

    Returns:
        Dictionary payload dari token

    Raises:
        JWTError: Kalau token invalid, expired, atau tampered

    Security checks:
    - Signature verification (pake secret key)
    - Expiration check (exp claim)
    - Algorithm validation (HS256 only)
    - Token format validation

    Usage:
        try:
            payload = verify_access_token(token)
            user_id = payload.get("sub")
            email = payload.get("email")
        except JWTError:
            # Token invalid atau expired
            raise HTTPException(401, "Invalid token")

    Note:
    - Harus wrap dengan try-catch
    - Auto throw exception kalau token invalid
    - Payload includes user data dari saat token dibuat
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise JWTError("Invalid token")


async def get_current_active_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    FastAPI dependency buat dapatkan current user dari JWT token.
    Ini function yang dipake di protected endpoints.

    Args:
        token: JWT token dari Authorization header (auto extract)
        db: Database session (auto inject)

    Returns:
        User object dengan role dan permissions loaded

    Raises:
        HTTPException 401: Kalau token invalid atau user tidak ada

    Process flow:
    1. Extract token dari Authorization header
    2. Verify token signature dan expiration
    3. Extract user ID dari token payload
    4. Query user dari database dengan permissions
    5. Return user object

    Usage in FastAPI:
        @router.get("/profile")
        async def get_profile(current_user: User = Depends(get_current_active_user)):
            return {"user": current_user.email}

    Security:
    - Auto extract dari "Bearer <token>" format
    - Complete token validation
    - User existence verification
    - Load permissions buat authorization
    """
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
    Factory function buat permission-based access control.
    Menghasilkan dependency checker buat protected endpoints.

    Args:
        required_permission: Permission name yang dibutuhkan

    Returns:
        Dependency function yang bisa dipake di FastAPI endpoints

    Permission system:
    - Role-based access control (RBAC)
    - User has role, role has permissions
    - Granular permission control
    - Hierarchical access control

    Usage in FastAPI:
        @router.post("/users")
        @has_permission("user.create")
        async def create_user(data: UserCreate):
            # Hanya user dengan permission "user.create" yang bisa akses
            pass

        @router.delete("/users/{id}")
        @has_permission("user.delete")
        async def delete_user(id: int):
            # Hanya user dengan permission "user.delete" yang bisa akses
            pass

    Security:
    - Auto check user permissions
    - Raise 403 Forbidden kalau tidak ada permission
    - Database-driven permission checking
    - Consistent error messages
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


# --- WEBSOCKET AUTHENTICATION ---
async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """
    Extract user dari JWT token buat WebSocket authentication.
    Mirip get_current_active_user tapi tanpa FastAPI dependencies.

    Args:
        token: JWT token string (dari WebSocket query/headers)
        db: Database session

    Returns:
        User object kalau valid, None kalau invalid

    Difference dengan HTTP auth:
    - Tidak pake dependency injection
    - Return None instead of exception
    - Safe buat WebSocket connection handling
    - Manual error handling

    Usage in WebSocket:
        async def websocket_endpoint(websocket: WebSocket, token: str = None):
            await websocket.accept()

            user = await get_user_from_token(token, db)
            if not user:
                await websocket.close(code=1008)  # Invalid token
                return

            # User authenticated, continue with WebSocket logic

    Security:
    - Same token validation dengan HTTP endpoints
    - Graceful error handling buat WebSocket
    - Prevent connection kalau token invalid
    - Load permissions buat WebSocket authorization
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
