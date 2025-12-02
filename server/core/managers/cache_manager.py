"""
Local Cache Manager
Manages disk usage for models with pinning and protected eviction
"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import threading

from core.structured_logger import get_structured_logger
from core.metrics_manager import get_metrics_manager

@dataclass
class CacheItem:
    path: Path
    size_bytes: int
    last_accessed: float
    pinned: bool
    pin_reason: Optional[str] = None

class CacheManager:
    """
    Manages local disk cache for models and artifacts.
    
    Features:
    - LRU Eviction: Removes old files to stay under quota.
    - Pinning: Protects critical models from eviction.
    - Atomic Operations: Safe deletion.
    - Quota Management: Enforces max cache size.
    """
    
    def __init__(self, cache_dir: Path, max_cache_bytes: int, min_free_bytes: int):
        self.struct_logger = get_structured_logger("CacheManager")
        self.metrics = get_metrics_manager()
        self.cache_dir = cache_dir
        self.max_cache_bytes = max_cache_bytes
        self.min_free_bytes = min_free_bytes
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        
        # In-memory state of cache items
        self._items: Dict[str, CacheItem] = {}
        self._scan_cache()
        
        self.struct_logger.info(
            "initialized",
            "Cache manager initialized",
            cache_dir=str(cache_dir),
            max_gb=round(max_cache_bytes / (1024**3), 2)
        )

    def _scan_cache(self):
        """Scan directory to build cache state"""
        with self._lock:
            existing_items = self._items.copy()
            self._items.clear()
            current_size = 0
            
            if not self.cache_dir.exists():
                return

            for entry in self.cache_dir.rglob("*"):
                if entry.is_file():
                    try:
                        stat = entry.stat()
                        # Group by model directory if possible, but for now treat files individually 
                        # or assume model_id maps to a subdir.
                        # Simplified: Assume direct files or folders in cache_dir are items.
                        # Let's assume 1 level depth for models: cache_dir/model_id/
                        
                        # Find the top-level item in cache_dir
                        rel_path = entry.relative_to(self.cache_dir)
                        top_level = rel_path.parts[0]
                        item_path = self.cache_dir / top_level
                        
                        if str(item_path) not in self._items:
                            # Calculate total size of this item (dir or file)
                            size = self._get_path_size(item_path)
                            last_access = item_path.stat().st_atime
                            
                            self._items[str(item_path)] = CacheItem(
                                path=item_path,
                                size_bytes=size,
                                last_accessed=last_access,
                                pinned=False # Default unpinned
                            )
                            
                            # Restore pin status if it existed
                            if str(item_path) in existing_items:
                                old_item = existing_items[str(item_path)]
                                self._items[str(item_path)].pinned = old_item.pinned
                                self._items[str(item_path)].pin_reason = old_item.pin_reason

                            current_size += size
                            
                    except Exception as e:
                        self.struct_logger.warning("scan_error", f"Error scanning {entry}: {e}")

    def _get_path_size(self, path: Path) -> int:
        """Get total size of file or directory"""
        if path.is_file():
            return path.stat().st_size
        total = 0
        for p in path.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
        return total

    def get_current_usage(self) -> int:
        """Get total bytes used"""
        with self._lock:
            return sum(item.size_bytes for item in self._items.values())

    def pin_model(self, model_id: str, reason: str) -> bool:
        """
        Pin a model to prevent eviction
        
        Args:
            model_id: ID of model (folder name in cache)
            reason: Reason for pinning
            
        Returns:
            True if pinned, False if not found
        """
        path = self.cache_dir / model_id
        key = str(path)
        
        with self._lock:
            if key in self._items:
                self._items[key].pinned = True
                self._items[key].pin_reason = reason
                self.struct_logger.info("model_pinned", f"Pinned model {model_id}", reason=reason)
                return True
            else:
                self.struct_logger.warning("pin_failed", f"Model {model_id} not found in cache")
                return False

    def unpin_model(self, model_id: str):
        """Unpin a model"""
        path = self.cache_dir / model_id
        key = str(path)
        
        with self._lock:
            if key in self._items:
                self._items[key].pinned = False
                self._items[key].pin_reason = None
                self.struct_logger.info("model_unpinned", f"Unpinned model {model_id}")

    def is_pinned(self, model_id: str) -> bool:
        """Check if a model is pinned"""
        path = self.cache_dir / model_id
        key = str(path)
        with self._lock:
            if key in self._items:
                return self._items[key].pinned
            return False

    def touch_model(self, model_id: str):
        """Update last accessed time"""
        path = self.cache_dir / model_id
        key = str(path)
        
        with self._lock:
            if key in self._items:
                self._items[key].last_accessed = time.time()
                # Also update filesystem
                try:
                    os.utime(path, None)
                except:
                    pass

    def ensure_space(self, required_bytes: int) -> bool:
        """
        Ensure enough space exists, evicting if necessary
        
        Args:
            required_bytes: Bytes needed
            
        Returns:
            True if space available/freed, False if impossible
        """
        with self._lock:
            current_usage = self.get_current_usage()
            available_capacity = self.max_cache_bytes - current_usage
            
            if available_capacity >= required_bytes:
                return True
            
            needed = required_bytes - available_capacity
            self.struct_logger.info("space_needed", f"Need {needed} bytes, triggering eviction")
            
            # Identify evictable items (not pinned)
            evictable = [
                item for item in self._items.values() 
                if not item.pinned
            ]
            
            # Sort by LRU (oldest access first)
            evictable.sort(key=lambda x: x.last_accessed)
            
            freed = 0
            evicted_count = 0
            
            for item in evictable:
                if freed >= needed:
                    break
                
                try:
                    if item.path.is_dir():
                        shutil.rmtree(item.path)
                    else:
                        item.path.unlink()
                    
                    freed += item.size_bytes
                    del self._items[str(item.path)]
                    evicted_count += 1
                    
                    self.struct_logger.info("evicted", f"Evicted {item.path.name}", size=item.size_bytes)
                    self.metrics.increment_counter("cache_eviction", 1, {"model_id": item.path.name})
                    
                except Exception as e:
                    self.struct_logger.error("eviction_failed", f"Failed to evict {item.path.name}: {e}")
            
            if freed >= needed:
                return True
            else:
                self.struct_logger.error(
                    "allocation_failed", 
                    "Could not free enough space",
                    needed=needed,
                    freed=freed,
                    pinned_usage=sum(i.size_bytes for i in self._items.values() if i.pinned)
                )
                return False

# Singleton
_cache_manager: Optional[CacheManager] = None

def get_cache_manager(
    cache_dir: Path = Path("ai-worker/cache"),
    max_bytes: int = 50 * 1024**3, # 50GB
    min_free: int = 2 * 1024**3    # 2GB
) -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir, max_bytes, min_free)
    return _cache_manager
