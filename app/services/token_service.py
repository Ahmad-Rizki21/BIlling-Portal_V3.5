# app/services/token_service.py
"""
Token Management Service - JWT token lifecycle management

Service ini handle semua aspek JWT token management dalam aplikasi.
Fokus pada refresh token mechanism dan token blacklisting buat security.

Token Management Features:
- JWT access token generation dan validation
- Refresh token rotation buat enhanced security
- Token blacklisting buat revocation
- User session management (logout dari semua devices)
- Automatic cleanup buat expired tokens

Security Features:
- Refresh token rotation (token baru setiap refresh)
- Token blacklisting dengan JWT ID tracking
- Automatic session revocation (logout all)
- Secure token hashing buat storage
- Protection against token reuse attacks

Token Types:
1. Access Token:
   - Short lifetime (15 menit)
   - Buat API access
   - Include user data dan permissions

2. Refresh Token:
   - Long lifetime (7 hari)
   - Buat dapatkan access token baru
   - Include JWT ID buat blacklisting
   - Rotation every refresh

Use Cases:
- User login dan session management
- API authentication
- Security enforcement
- Session revocation
- Token cleanup dan maintenance

Configuration:
- Access token lifetime: 15 menit
- Refresh token lifetime: 7 hari
- Token cleanup interval: 30 hari retention
- Hash algorithm: SHA256 buat token storage
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from ..models.user import User as UserModel
from ..models.token_blacklist import TokenBlacklist as TokenBlacklistModel
from ..config import settings
from ..schemas.token_blacklist import TokenBlacklistCreate
import hashlib

logger = logging.getLogger(__name__)


class TokenService:
    """
    JWT Token Management Service - Core token operations

    Service class yang handle semua JWT token operations, termasuk
    generation, validation, refresh, dan revocation.

    Service Configuration:
    - secret_key: JWT signing key dari environment
    - algorithm: JWT algorithm (HS256)
    - access_token_expire_minutes: Access token lifetime
    - refresh_token_expire_days: Refresh token lifetime

    Core Operations:
    1. Token Generation (access & refresh)
    2. Token Validation
    3. Token Refresh dengan rotation
    4. Token Blacklisting
    5. Session Management (logout all)
    6. Token Cleanup

    Security Features:
    - Refresh token rotation (prevent reuse)
    - Token blacklisting dengan JTI tracking
    - Automatic session revocation
    - Secure token hashing buat storage
    - Protection against replay attacks

    Integration Points:
    - Auth endpoints (login, refresh, logout)
    - Database models (TokenBlacklist)
    - Configuration management
    - Logging dan monitoring

    Performance Considerations:
    - Efficient database queries
    - Minimal memory footprint
    - Async operations throughout
    - Batch cleanup operations

    Usage Pattern:
    service = TokenService()
    access_token = service.create_access_token({"sub": "123"})
    refresh_token = service.create_refresh_token({"sub": "123"})
    """

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)  # Uses config value (120 minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create refresh token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        # Add refresh token specific claims
        to_encode.update(
            {"exp": expire, "iat": datetime.utcnow(), "type": "refresh", "jti": str(uuid.uuid4())}  # JWT ID for blacklisting
        )

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            return None

    async def blacklist_token(
        self,
        db: AsyncSession,
        jti: str,
        user_id: int,
        token_type: str,
        expires_at: datetime,
        reason: str = "Token expired or revoked",
    ) -> None:
        """Add token to blacklist, checking for existence first to ensure idempotency."""
        try:
            # Check if the token is already blacklisted
            if await self.is_token_blacklisted_db(db, jti):
                logger.warning(f"Attempted to blacklist an already blacklisted token (jti: {jti})")
                return  # Token is already blacklisted, so we do nothing.

            # Create blacklist entry
            blacklist_data = TokenBlacklistCreate(
                jti=jti,
                user_id=user_id,
                token_type=token_type,
                expires_at=expires_at,
                revoked=True,
                revoked_at=datetime.utcnow(),
                revoked_reason=reason,
            )

            db_blacklist = TokenBlacklistModel(**blacklist_data.model_dump())
            db.add(db_blacklist)
            await db.commit()
            logger.info(f"Token {jti} blacklisted for user {user_id}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to blacklist token {jti}: {e}")
            raise

    async def is_token_blacklisted_db(self, db: AsyncSession, jti: str) -> bool:
        """Check if token is blacklisted in database"""
        try:
            stmt = select(TokenBlacklistModel).where(and_(TokenBlacklistModel.jti == jti, TokenBlacklistModel.revoked == True))
            result = await db.execute(stmt)
            blacklist_entry = result.scalar_one_or_none()
            return blacklist_entry is not None
        except Exception as e:
            logger.error(f"Token blacklist check failed: {e}")
            return False

    async def refresh_access_token(self, db: AsyncSession, refresh_token: str) -> Optional[Tuple[str, str, int]]:
        """
        Refresh Access Token dengan Security Features

        Function ini implement refresh token mechanism dengan rotation dan security checks.
        Ini adalah core function buat maintain user session tanpa repeated login.

        Refresh Token Flow:
        1. Verify refresh token signature dan expiration
        2. Check token type (must be "refresh")
        3. Validate JWT ID (JTI) existence
        4. Check blacklist status
        5. Validate user existence
        6. Check user session revocation status
        7. Generate new token pair
        8. Blacklist old refresh token

        Security Features:
        - Token rotation (new refresh token setiap refresh)
        - Old token blacklisting (prevent reuse)
        - Session revocation checking (logout all)
        - User existence validation
        - Comprehensive audit logging

        Return Value:
        - Tuple(new_access_token, new_refresh_token, expires_in)
        - None kalau refresh token invalid atau expired

        Error Cases:
        - Invalid token signature -> None
        - Wrong token type -> None + warning log
        - Token already blacklisted -> None + warning
        - User not found -> None + warning
        - User session revoked -> None + warning

        Args:
            db: AsyncSession database connection
            refresh_token: Refresh token yang mau dipake

        Returns:
            Optional[Tuple[str, str, int]]: New tokens atau None kalau failed
        """
        payload = self.verify_token(refresh_token)
        if not payload:
            return None

        if payload.get("type") != "refresh":
            logger.warning("Invalid token type used for refresh")
            return None

        jti = payload.get("jti")
        if not jti:
            logger.warning("Refresh token missing jti")
            return None

        if await self.is_token_blacklisted_db(db, jti):
            logger.warning(f"Attempted to use blacklisted refresh token (jti: {jti})")
            return None

        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Refresh token missing sub")
            return None

        user = await db.get(UserModel, int(user_id))
        if not user:
            logger.warning(f"User {user_id} not found for refresh token")
            return None

        # Check for 'logout all'
        if user.revoked_before and user.revoked_before > datetime.fromtimestamp(payload.get("iat", 0)):
            logger.warning(f"Attempted to use a revoked (logout all) refresh token for user {user.id}")
            return None

        # Create new tokens
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        new_access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email}, expires_delta=access_token_expires
        )
        new_refresh_token = self.create_refresh_token(data={"sub": str(user.id), "email": user.email})

        # Blacklist the old refresh token
        old_exp = datetime.fromtimestamp(payload.get("exp", 0))
        await self.blacklist_token(db, jti, int(user_id), "refresh", old_exp, "Token refreshed - old token invalidated")

        return new_access_token, new_refresh_token, int(access_token_expires.total_seconds())

    async def revoke_all_user_tokens(self, db: AsyncSession, user_id: int) -> None:
        """
        Revoke All User Tokens - Forced logout dari semua devices

        Function ini revoke semua refresh token user dengan setting revoked_before
        timestamp. Ini memaksa logout dari semua devices yang sedang aktif.

        Revocation Mechanism:
        - Set user.revoked_before = current time
        - Semua refresh token yang issued sebelum waktu ini akan invalid
        - Tidak perlu blacklist individual tokens
        - Efficient buat mass session termination

        Security Benefits:
        - Immediate session termination
        - Protection against compromised sessions
    - Emergency response untuk security incidents
        - Account takeover mitigation

        Use Cases:
        - User request "logout dari semua devices"
        - Security incident response
        - Password change forced logout
        - Suspicious activity detection
        - Admin session management

        Implementation Details:
        - Update user model dengan revoked_before timestamp
        - Token validation akan check field ini
        - All existing refresh tokens become invalid
        - New token issued setelah revocation

        Error Handling:
        - Database rollback on failure
        - Comprehensive error logging
        - Atomic operation guarantee

        Args:
            db: AsyncSession database connection
            user_id: ID user yang tokens mau direvoke

        Raises:
            Exception: Database operation failure (dengan rollback)
        """
        try:
            user = await db.get(UserModel, user_id)
            if user:
                user.revoked_before = datetime.utcnow()
                db.add(user)
                await db.commit()
                logger.info(f"All tokens for user {user_id} have been revoked")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to revoke all tokens for user {user_id}: {e}")
            raise

    def hash_token_for_storage(self, token: str) -> str:
        """Hash token for secure storage (not used in JWT but for reference)"""
        return hashlib.sha256(token.encode()).hexdigest()

    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """Remove expired tokens from blacklist to prevent table bloat"""
        try:
            # Get current time
            now = datetime.utcnow()

            # Delete expired blacklist entries (older than 30 days)
            thirty_days_ago = now - timedelta(days=30)

            stmt = select(TokenBlacklistModel).where(TokenBlacklistModel.expires_at < thirty_days_ago)
            result = await db.execute(stmt)
            expired_tokens = result.scalars().all()

            count = len(expired_tokens)
            for token in expired_tokens:
                await db.delete(token)

            await db.commit()
            logger.info(f"Cleaned up {count} expired tokens from blacklist")

            return count

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0


# Global instance
token_service = TokenService()


def get_token_service() -> TokenService:
    """Dependency injection for token service"""
    return token_service
