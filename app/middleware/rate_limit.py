# app/middleware/rate_limit.py
"""
Rate limiting middleware untuk melindungi API dari brute force attacks
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
    def __init__(self):
        # Store rate limit data in memory (for production, use Redis)
        self.requests: Dict[str, list] = defaultdict(list)
        self.failed_logins: Dict[str, list] = defaultdict(list)  # Track failed logins
        self.blocked_ips: Dict[str, float] = {}  # IP -> unblock time
        self.blocked_users: Dict[str, float] = {}  # Username -> unblock time

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP address"""
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
        """Generate unique key for rate limiting"""
        return hashlib.md5(f"{identifier}:{endpoint}".encode()).hexdigest()

    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier (IP or username) is blocked"""
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
        """Record failed login attempt"""
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
        """Reset failed login attempts on successful login"""
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
        Check if request is rate limited

        Returns:
            tuple: (is_limited: bool, info: dict)
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
