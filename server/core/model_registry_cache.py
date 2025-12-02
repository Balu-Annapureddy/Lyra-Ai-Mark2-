"""
Model Registry Caching System
Caches compatible model lists to avoid recomputing on every request
"""

import time
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from core.structured_logger import get_structured_logger


@dataclass
class CacheEntry:
    """Cache entry with data and metadata"""
    data: Any
    created_at: float
    file_hash: str
    hits: int = 0


class ModelRegistryCache:
    """
    Caching system for model registry
    
    Features:
    - Cache compatible model lists
    - Invalidate on file changes (via hash)
    - TTL-based expiration
    - Cache statistics
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time-to-live for cache entries (default 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self.struct_logger = get_structured_logger("ModelRegistryCache")
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0
        }
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file contents for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def get(
        self,
        key: str,
        file_path: Optional[Path] = None
    ) -> Optional[Any]:
        """
        Get cached data
        
        Args:
            key: Cache key
            file_path: Optional file path for hash-based invalidation
            
        Returns:
            Cached data or None if not found/expired/invalid
        """
        if key not in self._cache:
            self._stats["misses"] += 1
            return None
        
        entry = self._cache[key]
        
        # Check TTL
        if time.time() - entry.created_at > self.ttl_seconds:
            self.struct_logger.debug(
                "cache_expired",
                f"Cache entry expired: {key}",
                key=key,
                age_seconds=time.time() - entry.created_at
            )
            del self._cache[key]
            self._stats["misses"] += 1
            self._stats["invalidations"] += 1
            return None
        
        # Check file hash if provided
        if file_path:
            current_hash = self._get_file_hash(file_path)
            if current_hash != entry.file_hash:
                self.struct_logger.debug(
                    "cache_invalidated",
                    f"Cache invalidated due to file change: {key}",
                    key=key,
                    file_path=str(file_path)
                )
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["invalidations"] += 1
                return None
        
        # Cache hit
        entry.hits += 1
        self._stats["hits"] += 1
        
        self.struct_logger.debug(
            "cache_hit",
            f"Cache hit: {key}",
            key=key,
            entry_hits=entry.hits
        )
        
        return entry.data
    
    def set(
        self,
        key: str,
        data: Any,
        file_path: Optional[Path] = None
    ):
        """
        Set cached data
        
        Args:
            key: Cache key
            data: Data to cache
            file_path: Optional file path for hash-based invalidation
        """
        file_hash = self._get_file_hash(file_path) if file_path else ""
        
        self._cache[key] = CacheEntry(
            data=data,
            created_at=time.time(),
            file_hash=file_hash
        )
        
        self.struct_logger.debug(
            "cache_set",
            f"Cache entry created: {key}",
            key=key,
            has_file_hash=bool(file_hash)
        )
    
    def invalidate(self, key: str):
        """Invalidate a specific cache entry"""
        if key in self._cache:
            del self._cache[key]
            self._stats["invalidations"] += 1
            self.struct_logger.debug(
                "cache_invalidated",
                f"Cache entry invalidated: {key}",
                key=key
            )
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        self._stats["invalidations"] += count
        
        self.struct_logger.info(
            "cache_cleared",
            f"Cache cleared: {count} entries removed",
            entries_cleared=count
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 3),
            "cached_entries": len(self._cache),
            "ttl_seconds": self.ttl_seconds
        }
