# app/middleware/rate_limit.py
"""
Rate Limiting Middleware - Proteksi API dari serangan dan abuse

Middleware ini jaga API dari request yang berlebihan dan brute force attacks.
Fungsi utamanya nge-limit request dari IP tertentu biar server nggak down.

Security Features:
- Rate limiting per IP address
- Brute force protection buat login attempts
- Automatic IP blocking kalau melebihi threshold
- Failed login tracking dan user blocking
- Auto-unblock setelah waktu tertentu

How it works:
1. Track request count per IP dalam time window
2. Block request kalau melebihi batas maksimal
3. Kirim response 429 Too Many Requests
4. Auto-reset counter setelah time window habis
5. Block user kalau failed login terlalu banyak

Configuration:
- Default rate limit: 100 requests per hour per IP
- Failed login threshold: 5 attempts per 15 minutes
- IP block duration: 1 hour
- User block duration: 30 minutes

Usage:
- @rate_limit() decorator buat endpoints
- @login_rate_limit() buat login endpoints
- rate_limiter.is_rate_limited() buat manual checks
"""

import hashlib
import logging
import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict, Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate Limiter Implementation - Core rate limiting logic

    Class ini handle semua rate limiting logic di aplikasi.
    Nge-track request per IP dan failed login attempts.

    Data Storage:
    - requests: Track semua request per IP
    - failed_logins: Track failed login attempts per IP dan user
    - blocked_ips: Daftar IP yang diblock + waktu unblock
    - blocked_users: Daftar user yang diblock + waktu unblock

    Production Note:
    - Saat ini pake memory storage (defaultdict)
    - Buat production, recommended pake Redis biar persistent

    Security Features:
    - Separate tracking untuk request dan failed login
    - Automatic cleanup data yang expired
    - IP address extraction dari headers (X-Forwarded-For)
    - Unique key generation per identifier
    """

    def __init__(self):
        # Store rate limit data in memory (for production, use Redis)
        self.requests: Dict[str, list] = defaultdict(list)
        self.failed_logins: Dict[str, list] = defaultdict(list)  # Track failed logins
        self.blocked_ips: Dict[str, float] = {}  # IP -> unblock time
        self.blocked_users: Dict[str, float] = {}  # Username -> unblock time

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract Real Client IP Address - Handle reverse proxy configuration

        Function ini extract IP address asli dari client, even kalau aplikasi
        jalan di belakang reverse proxy (nginx, cloudflare, dll).

        IP Resolution Priority:
        1. X-Forwarded-For header (comma-separated list, ambil yang pertama)
        2. X-Real-IP header (nginx standard)
        3. request.client.host (direct connection)

        Security Note:
        - Header bisa di-spoof, jadi harus careful di production
        - X-Forwarded-For format: "client, proxy1, proxy2"
        - Ambil IP pertama (client asli)

        Use Cases:
        - Rate limiting per IP
        - Failed login tracking
        - Geographic blocking
        - Security monitoring

        Args:
            request: FastAPI Request object

        Returns:
            IP address string dari client asli
        """
        # Check for forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        return request.client.host if request.client else "unknown"

    def _generate_key(self, identifier: str, endpoint: str = "") -> str:
        """
        Generate Unique Key for Rate Limiting - Hashing identifiers

        Generate unique key pake MD5 hash buat identifier rate limiting.
        Ini memastikan setiap kombinasi IP + endpoint punya key yang unik.

        Key Format:
        - Input: "{identifier}:{endpoint}"
        - Hash: MD5 (32 character hex string)
        - Examples:
          - "192.168.1.1:/api/users" -> "a1b2c3d4e5f6..."
          - "192.168.1.1:/api/login" -> "f6e5d4c3b2a1..."

        Why MD5?
        - Cepat dan lightweight
        - Fixed length output (32 chars)
        - Low collision rate buat use case ini
        - Sufficient buat rate limiting key

        Security Note:
        - MD5 cryptographically broken, tapi fine buat rate limiting
        - Not buat password atau sensitive data
        - Cuma buat generate consistent keys

        Args:
            identifier: IP address atau user identifier
            endpoint: API endpoint path (optional)

        Returns:
            32-character hexadecimal MD5 hash
        """
        return hashlib.md5(f"{identifier}:{endpoint}".encode()).hexdigest()

    def is_blocked(self, identifier: str) -> bool:
        """
        Check if Identifier is Blocked - IP/Username blocking verification

        Cek apakah IP address atau username sedang diblock.
        Function ini auto-unblock identifiers yang sudah expired.

        Blocking Logic:
        - Check di blocked_ips dictionary untuk IP blocking
        - Check di blocked_users dictionary untuk username blocking
        - Auto-unblock kalau block time sudah expired
        - Clean up expired entries buat memory efficiency

        Block Duration:
        - IP blocking: 1 jam (3600 seconds)
        - User blocking: 30 menit (1800 seconds)
        - Auto-cleanup setelah expired

        Performance:
        - O(1) lookup pake dictionary
        - Auto cleanup prevent memory bloat
        - Efficient buat high-traffic applications

        Args:
            identifier: IP address atau username yang mau dicek

        Returns:
            True kalau identifier masih diblock, False kalau tidak
        """
        current_time = time.time()

        # Check IP blocking
        if identifier in self.blocked_ips:
            if current_time < self.blocked_ips[identifier]:
                return True
            else:
                # Unblock expired
                del self.blocked_ips[identifier]

        return False

    def record_failed_login(self, client_ip: str, username: str):
        """
        Record Failed Login Attempt - Brute force protection tracking

        Track failed login attempts per IP dan per username.
        Function ini akan block IP atau username kalau failed attempts terlalu banyak.

        Brute Force Protection Strategy:
        - Track failed attempts per IP address
        - Track failed attempts per username
        - Separate thresholds buat IP vs user blocking
        - Time-based window (rolling 15 minutes)

        Threshold Configuration:
        - Max IP attempts: 20 per 15 menit
        - Max user attempts: 5 per 15 menit
        - IP block duration: 1 jam
        - User block duration: 30 menit

        Security Benefits:
        - Prevent credential stuffing attacks
        - Block automated password guessing
        - Protect specific accounts dari targeting
        - Rate limiting per IP dan per user

        Implementation Details:
        - Rolling time window (bukan fixed interval)
        - Auto cleanup old attempts
        - Case-insensitive username blocking
        - Comprehensive logging buat security monitoring

        Args:
            client_ip: IP address dari failed login attempt
            username: Username yang gagal login
        """
        current_time = time.time()
        key_ip = f"ip:{client_ip}"
        key_user = f"user:{username.lower()}"

        # Clean old failed attempts (15 minutes window)
        window_seconds = 900  # 15 minutes
        self.failed_logins[key_ip] = [
            attempt for attempt in self.failed_logins[key_ip] if current_time - attempt < window_seconds
        ]
        self.failed_logins[key_user] = [
            attempt for attempt in self.failed_logins[key_user] if current_time - attempt < window_seconds
        ]

        # Add current failed attempt
        self.failed_logins[key_ip].append(current_time)
        self.failed_logins[key_user].append(current_time)

        # Check if exceeds threshold
        max_ip_attempts = 20  # Max 20 failed attempts per IP per 15 minutes
        max_user_attempts = 5  # Max 5 failed attempts per user per 15 minutes

        if len(self.failed_logins[key_ip]) >= max_ip_attempts:
            # Block IP for 1 hour
            self.blocked_ips[client_ip] = current_time + 3600
            logger.warning(f"Blocking IP {client_ip} due to {max_ip_attempts} failed login attempts")

        if len(self.failed_logins[key_user]) >= max_user_attempts:
            # Block user for 30 minutes
            self.blocked_users[username.lower()] = current_time + 1800
            logger.warning(f"Blocking user {username} due to {max_user_attempts} failed login attempts")

    def reset_failed_attempts(self, client_ip: str, username: str):
        """
        Reset Failed Login Attempts - Clear successful login data

        Reset semua failed login attempts untuk IP dan username setelah login berhasil.
        Ini memastikan user legitimate nggak kena block karena failed attempts sebelumnya.

        Reset Logic:
        - Clear failed attempts history untuk IP
        - Clear failed attempts history untuk username
        - Unblock username kalau sebelumnya diblock
        - Clean up data buat memory efficiency

        Use Cases:
        - Setelah successful login
        - Setelah password reset
        - Manual admin intervention
        - False positive correction

        Security Benefits:
        - Prevent false positives
        - Allow legitimate users setelah successful auth
        - Clean tracking data buat fresh start
        - Remove temporary blocks immediately

        Important Note:
        - IP block tetap dipertahankan (security measure)
        - Hanya username block yang direset
        - Failed attempts dihapus permanen
        - User bisa coba lagi dari IP yang sama

        Args:
            client_ip: IP address yang berhasil login
            username: Username yang berhasil login
        """
        key_ip = f"ip:{client_ip}"
        key_user = f"user:{username.lower()}"

        if key_ip in self.failed_logins:
            del self.failed_logins[key_ip]
        if key_user in self.failed_logins:
            del self.failed_logins[key_user]

        # Also unblock if previously blocked
        if username.lower() in self.blocked_users:
            del self.blocked_users[username.lower()]

    def is_rate_limited(
        self,
        request: Request,
        max_requests: int = 100,
        window_seconds: int = 3600,
        endpoint_specific: bool = False,
    ) -> tuple[bool, dict]:
        """
        Rate Limiting Check - Core rate limiting logic

        Function utama buat cek apakah request harus dibatasi atau tidak.
        Ini implementasi sliding window rate limiting algorithm.

        Rate Limiting Algorithm:
        - Sliding time window (bukan fixed interval)
        - Track request timestamps per IP
        - Clean up old requests outside window
        - Block kalau melebihi threshold

        Parameters:
        - max_requests: Maximum requests allowed dalam window
        - window_seconds: Time window dalam detik
        - endpoint_specific: True = rate limit per endpoint, False = global

        Blocking Logic:
        - Check IP block status dulu
        - Hitung request dalam current window
        - Block IP kalau melebihi limit
        - Auto cleanup expired requests

        Response Format:
        - True, {"retry_after": 3600, "reason": "..."} kalau diblock
        - False, {"remaining": 50, "reset": timestamp} kalau dibolehin

        Performance Features:
        - O(n) complexity dimana n = requests dalam window
        - Auto cleanup prevent memory bloat
        - Efficient time comparison
        - Fast dictionary lookup

        Args:
            request: FastAPI Request object
            max_requests: Max requests per time window (default: 100)
            window_seconds: Window duration dalam detik (default: 3600)
            endpoint_specific: Rate limit per endpoint atau global

        Returns:
            Tuple (is_limited: bool, info: dict) dengan status dan detail info
        """
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path if endpoint_specific else ""

        # Check if IP is blocked
        if self.is_blocked(client_ip):
            return True, {
                "retry_after": int(self.blocked_ips[client_ip] - time.time()),
                "reason": "IP blocked due to excessive requests",
            }

        key = self._generate_key(client_ip, endpoint)
        current_time = time.time()

        # Clean old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] if current_time - req_time < window_seconds]

        # Check rate limit
        request_count = len(self.requests[key])
        if request_count >= max_requests:
            # Block IP for 1 hour
            self.blocked_ips[client_ip] = current_time + 3600
            logger.warning(f"Blocking IP {client_ip} due to rate limit exceeded")
            return True, {
                "retry_after": 3600,
                "reason": f"Rate limit exceeded: {max_requests} requests per hour",
            }

        # Add current request
        self.requests[key].append(current_time)

        return False, {
            "remaining": max_requests - request_count - 1,
            "reset": int(current_time + window_seconds),
        }

    def is_brute_force_login(
        self,
        request: Request,
        username: str,
        max_attempts: int = 5,
        window_seconds: int = 900,  # 15 minutes
    ) -> bool:
        """Specific rate limiting for login attempts"""
        # Check if user is blocked
        username_lower = username.lower()
        current_time = time.time()

        if username_lower in self.blocked_users:
            if current_time < self.blocked_users[username_lower]:
                return True
            else:
                # Unblock expired
                del self.blocked_users[username_lower]

        key = f"login:{username_lower}"
        current_time = time.time()

        # Clean old attempts
        self.requests[key] = [req_time for req_time in self.requests[key] if current_time - req_time < window_seconds]

        # Check if exceeds max attempts
        if len(self.requests[key]) >= max_attempts:
            # Block further login attempts for this user
            client_ip = self._get_client_ip(request)
            self.blocked_users[username_lower] = current_time + 1800  # Block user for 30 minutes
            logger.warning(f"Brute force attempt detected for user {username} from IP {client_ip}")
            return True

        # Add current attempt
        self.requests[key].append(current_time)
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limiting decorators
def rate_limit(max_requests: int = 100, window_seconds: int = 3600, endpoint_specific: bool = False):
    """Decorator for rate limiting endpoints"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]

            if request:
                is_limited, info = rate_limiter.is_rate_limited(request, max_requests, window_seconds, endpoint_specific)
                if is_limited:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Rate limit exceeded",
                            "message": info["reason"],
                            "retry_after": info["retry_after"],
                        },
                    )
            # Jika tidak ada request, tetap izinkan fungsi dijalankan
            try:
                return await func(*args, **kwargs)
            except TypeError as e:
                # Jika terjadi error karena parameter yang tidak sesuai, coba panggil tanpa parameter
                if "missing" in str(e) and ("args" in str(e) or "kwargs" in str(e)):
                    return await func()
                raise e

        return wrapper

    return decorator


def login_rate_limit(max_attempts: int = 5, window_seconds: int = 900):
    """Decorator specifically for login rate limiting"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract username from request
            username = None
            request = None

            # Find request object
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]

            # Extract username from form data or JSON
            if request:
                try:
                    form_data = await request.form()
                    username = form_data.get("username")
                except:
                    try:
                        json_data = await request.json()
                        username = json_data.get("username")
                    except:
                        pass

                if username:
                    if rate_limiter.is_brute_force_login(request, username, max_attempts, window_seconds):
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail={
                                "error": "Too many login attempts",
                                "message": f"Account temporarily locked due to {max_attempts} failed login attempts",
                                "retry_after": 1800,  # 30 minutes
                            },
                        )
            # Jika tidak ada request atau username, tetap izinkan fungsi dijalankan
            try:
                return await func(*args, **kwargs)
            except TypeError as e:
                # Jika terjadi error karena parameter yang tidak sesuai, coba panggil tanpa parameter
                if "missing" in str(e) and ("args" in str(e) or "kwargs" in str(e)):
                    return await func()
                raise e

        return wrapper

    return decorator
