"""
Cache Service untuk Static Data Caching.
Mengimplementasi Redis-like in-memory cache untuk data yang tidak sering berubah.
"""

import json
import time
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger("app.cache_service")

# In-memory cache storage (dapat diganti dengan Redis di production)
_cache_store: Dict[str, Any] = {}  # type: ignore
_cache_stats: Dict[str, int] = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

# Cache configuration
CACHE_CONFIG = {
    "harga_layanan_ttl": 3600,  # 1 jam
    "paket_layanan_ttl": 3600,  # 1 jam
    "brand_data_ttl": 1800,  # 30 menit
    "mikrotik_servers_ttl": 300,  # 5 menit
    "user_permissions_ttl": 600,  # 10 menit
    "dashboard_cache_ttl": 300,  # 5 menit
    "max_cache_size": 1000,  # Maximum items in cache
}


class CacheItem:
    """Item cache dengan TTL dan metadata."""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Cek apakah cache item sudah expired."""
        return time.time() > self.expires_at

    def touch(self):
        """Update last access time dan counter."""
        self.access_count += 1
        self.last_accessed = time.time()


def _get_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key yang konsisten."""
    key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _evict_expired_items():
    """Hapus cache items yang sudah expired."""
    expired_keys = [key for key, item in _cache_store.items() if item.get("expires_at", 0) < time.time()]

    for key in expired_keys:
        del _cache_store[key]
        _cache_stats["evictions"] += 1

    if expired_keys:
        logger.debug(f"Evicted {len(expired_keys)} expired cache items")


def _evict_lru_items(count: int = 1):
    """Hapus cache items dengan LRU (Least Recently Used) policy."""
    if len(_cache_store) <= CACHE_CONFIG["max_cache_size"]:
        return

    # Sort by last accessed time
    sorted_items = sorted(_cache_store.items(), key=lambda x: x[1].get("last_accessed", 0))

    # Remove oldest items
    for i in range(min(count, len(sorted_items))):
        key = sorted_items[i][0]
        del _cache_store[key]
        _cache_stats["evictions"] += 1


def _get_cache_stats() -> Dict[str, int]:
    """Get cache statistics untuk monitoring."""
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

    return {
        "stats": _cache_stats.copy(),
        "hit_rate_percent": round(hit_rate, 2),
        "cache_size": len(_cache_store),
        "max_size": CACHE_CONFIG["max_cache_size"],
        "utilization_percent": round(len(_cache_store) / CACHE_CONFIG["max_cache_size"] * 100, 2),
    }


def get_from_cache(key: str) -> Optional[Any]:
    """Ambil data dari cache."""
    _evict_expired_items()

    if key in _cache_store:
        item = _cache_store[key]
        if item.get("expires_at", 0) >= time.time():
            # Update last access time
            item["last_accessed"] = time.time()
            item["access_count"] = item.get("access_count", 0) + 1
            _cache_stats["hits"] += 1
            logger.debug(f"Cache hit: {key}")
            return item.get("value")
        else:
            # Remove expired item
            del _cache_store[key]
            _cache_stats["evictions"] += 1

    _cache_stats["misses"] += 1
    logger.debug(f"Cache miss: {key}")
    return None


def set_to_cache(key: str, value: Any, ttl: int) -> None:
    """Simpan data ke cache."""

    # Enforce cache size limit
    if len(_cache_store) >= CACHE_CONFIG["max_cache_size"]:
        _evict_lru_items()

    _cache_store[key] = {
        "value": value,
        "created_at": time.time(),
        "expires_at": time.time() + ttl,
        "access_count": 0,
        "last_accessed": time.time(),
    }
    _cache_stats["sets"] += 1
    logger.debug(f"Cache set: {key} (TTL: {ttl}s)")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring."""
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

    return {
        "stats": _cache_stats.copy(),
        "hit_rate_percent": round(hit_rate, 2),
        "cache_size": len(_cache_store),
        "max_size": CACHE_CONFIG["max_cache_size"],
        "utilization_percent": round(len(_cache_store) / CACHE_CONFIG["max_cache_size"] * 100, 2),
    }


def clear_all_cache() -> int:
    """Clear semua cache data."""
    cleared_count = len(_cache_store)
    _cache_store.clear()
    _cache_stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    logger.info(f"Cleared {cleared_count} cache items")
    return cleared_count


def _evict_data_caches():
    """Invalidate semua data-related cache saat ada perubahan data."""
    patterns = ["harga_layanan", "paket_layanan", "brand_data", "dashboard_data"]

    for pattern in patterns:
        invalidate_cache_pattern(pattern)

    logger.info("Invalidated all data caches due to data changes")


def cache_result(ttl: int, key_prefix: str = ""):
    """
    Decorator untuk cache hasil function.

    Usage:
    @cache_result(ttl=3600, key_prefix="harga_layanan")
    async def get_harga_layanan():
        # Database query logic
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _get_cache_key(f"{key_prefix}:{func.__name__}", args=args, kwargs=kwargs)

            # Try to get from cache
            cached_result = get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            set_to_cache(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate cache items yang match dengan pattern."""
    keys_to_remove = [key for key in _cache_store.keys() if pattern in key]

    for key in keys_to_remove:
        del _cache_store[key]

    if keys_to_remove:
        logger.info(f"Invalidated {len(keys_to_remove)} cache items matching '{pattern}'")


async def get_cached_harga_layanan(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get harga layanan data dengan cache."""
    from ..models.harga_layanan import HargaLayanan

    cache_key = _get_cache_key("harga_layanan_all")
    cached_data = get_from_cache(cache_key)

    if cached_data is not None:
        return cached_data  # type: ignore

    # Query database
    stmt = select(HargaLayanan).order_by(HargaLayanan.brand)
    result = await db.execute(stmt)
    items = result.scalars().all()

    # Transform to dict for caching
    data = [
        {
            "id": item.id,
            "id_brand": item.id_brand,
            "brand": item.brand,
            "layanan": item.layanan,
            "harga": float(item.harga),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]

    set_to_cache(cache_key, data, CACHE_CONFIG["harga_layanan_ttl"])
    return data


async def get_cached_paket_layanan(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get paket layanan data dengan cache."""
    from ..models.paket_layanan import PaketLayanan

    cache_key = _get_cache_key("paket_layanan_all")
    cached_data = get_from_cache(cache_key)

    if cached_data is not None:
        return cached_data  # type: ignore

    # Query database
    stmt = select(PaketLayanan).order_by(PaketLayanan.kecepatan)
    result = await db.execute(stmt)
    items = result.scalars().all()

    # Transform to dict for caching
    data = [
        {
            "id": item.id,
            "kecepatan": item.kecepatan,
            "harga": float(item.harga),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]

    set_to_cache(cache_key, data, CACHE_CONFIG["paket_layanan_ttl"])
    return data


async def get_cached_brand_data(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get brand data dengan cache."""
    from ..models.harga_layanan import HargaLayanan

    cache_key = _get_cache_key("brand_data_all")
    cached_data = get_from_cache(cache_key)

    if cached_data is not None:
        return cached_data  # type: ignore

    # Query distinct brands
    stmt = select(HargaLayanan.id_brand, HargaLayanan.brand).distinct().order_by(HargaLayanan.brand)
    result = await db.execute(stmt)
    items = result.all()

    # Transform to dict for caching
    data = [{"id_brand": item.id_brand, "brand": item.brand} for item in items]

    set_to_cache(cache_key, data, CACHE_CONFIG["brand_data_ttl"])
    return data


def invalidate_data_caches():
    """Invalidate semua data-related cache saat ada perubahan data."""
    patterns = ["harga_layanan", "paket_layanan", "brand_data", "dashboard_data"]

    for pattern in patterns:
        invalidate_cache_pattern(pattern)

    logger.info("Invalidated all data caches due to data changes")
