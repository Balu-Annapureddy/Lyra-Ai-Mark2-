"""
Temporary Files Manager
Manages temporary files with automatic cleanup and policy-based storage
"""

import logging
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import atexit
import threading

from core.paths import get_cache_dir
from core.errors import StateError

logger = logging.getLogger(__name__)


class TempManager:
    """
    Manages temporary files and directories
    Automatic cleanup based on policies
    """
    
    def __init__(
        self,
        temp_dir: Optional[Path] = None,
        max_age_hours: int = 24,
        max_size_mb: int = 1000
    ):
        """
        Initialize temp manager
        
        Args:
            temp_dir: Temporary directory (defaults to cache dir)
            max_age_hours: Maximum age for temp files
            max_size_mb: Maximum total size in MB
        """
        self.temp_dir = temp_dir or (get_cache_dir() / "temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_age_hours = max_age_hours
        self.max_size_mb = max_size_mb
        
        self._tracked_files: Dict[str, Path] = {}
        self._lock = threading.Lock()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
        
        logger.info(f"TempManager initialized: {self.temp_dir}")
    
    def create_temp_file(
        self,
        prefix: str = "lyra_",
        suffix: str = "",
        content: Optional[str] = None
    ) -> Path:
        """
        Create temporary file
        
        Args:
            prefix: Filename prefix
            suffix: Filename suffix (e.g., ".txt")
            content: Optional content to write
        
        Returns:
            Path to temp file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}{timestamp}{suffix}"
        file_path = self.temp_dir / filename
        
        if content:
            file_path.write_text(content, encoding='utf-8')
        else:
            file_path.touch()
        
        with self._lock:
            self._tracked_files[str(file_path)] = file_path
        
        logger.debug(f"Created temp file: {file_path}")
        
        return file_path
    
    def create_temp_dir(
        self,
        prefix: str = "lyra_dir_"
    ) -> Path:
        """
        Create temporary directory
        
        Args:
            prefix: Directory name prefix
        
        Returns:
            Path to temp directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dir_name = f"{prefix}{timestamp}"
        dir_path = self.temp_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            self._tracked_files[str(dir_path)] = dir_path
        
        logger.debug(f"Created temp dir: {dir_path}")
        
        return dir_path
    
    def delete_temp_file(self, file_path: Path):
        """
        Delete temporary file or directory
        
        Args:
            file_path: Path to delete
        """
        try:
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            
            with self._lock:
                if str(file_path) in self._tracked_files:
                    del self._tracked_files[str(file_path)]
            
            logger.debug(f"Deleted temp file: {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to delete temp file: {e}")
    
    def cleanup_old_files(self):
        """Remove files older than max_age_hours"""
        cutoff = datetime.now() - timedelta(hours=self.max_age_hours)
        removed_count = 0
        
        for item in self.temp_dir.iterdir():
            try:
                # Check modification time
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                
                if mtime < cutoff:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    
                    with self._lock:
                        if str(item) in self._tracked_files:
                            del self._tracked_files[str(item)]
                    
                    removed_count += 1
            
            except Exception as e:
                logger.error(f"Failed to cleanup {item}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old temp files")
    
    def cleanup_by_size(self):
        """Remove oldest files if total size exceeds max_size_mb"""
        # Get all files with sizes and mtimes
        files_info = []
        total_size = 0
        
        for item in self.temp_dir.rglob('*'):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    mtime = item.stat().st_mtime
                    files_info.append((item, size, mtime))
                    total_size += size
                except:
                    pass
        
        # Check if cleanup needed
        max_size_bytes = self.max_size_mb * 1024 * 1024
        if total_size <= max_size_bytes:
            return
        
        # Sort by modification time (oldest first)
        files_info.sort(key=lambda x: x[2])
        
        # Remove oldest files until under limit
        removed_count = 0
        for file_path, size, _ in files_info:
            try:
                file_path.unlink()
                total_size -= size
                removed_count += 1
                
                with self._lock:
                    if str(file_path) in self._tracked_files:
                        del self._tracked_files[str(file_path)]
                
                if total_size <= max_size_bytes:
                    break
            
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} files to reduce size")
    
    def cleanup_all(self):
        """Remove all temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            with self._lock:
                self._tracked_files.clear()
            
            logger.info("Cleaned up all temp files")
        
        except Exception as e:
            logger.error(f"Failed to cleanup all temp files: {e}")
    
    def get_temp_size(self) -> int:
        """
        Get total size of temp directory in bytes
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        
        for item in self.temp_dir.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except:
                    pass
        
        return total_size
    
    def get_temp_count(self) -> int:
        """
        Get number of temp files
        
        Returns:
            Number of files
        """
        return sum(1 for _ in self.temp_dir.rglob('*') if _.is_file())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get temp directory statistics"""
        return {
            "temp_dir": str(self.temp_dir),
            "total_size_mb": self.get_temp_size() / (1024 ** 2),
            "file_count": self.get_temp_count(),
            "tracked_files": len(self._tracked_files),
            "max_age_hours": self.max_age_hours,
            "max_size_mb": self.max_size_mb
        }


# Global temp manager instance
_global_temp_manager: Optional[TempManager] = None


def get_temp_manager() -> TempManager:
    """Get global temp manager instance"""
    global _global_temp_manager
    if _global_temp_manager is None:
        _global_temp_manager = TempManager()
    return _global_temp_manager


if __name__ == "__main__":
    # Test temp manager
    print("Testing Temp Manager")
    print("=" * 50)
    
    temp_mgr = TempManager()
    
    # Create temp file
    temp_file = temp_mgr.create_temp_file(suffix=".txt", content="Hello World")
    print(f"Created: {temp_file}")
    
    # Create temp dir
    temp_dir = temp_mgr.create_temp_dir()
    print(f"Created: {temp_dir}")
    
    # Get stats
    stats = temp_mgr.get_stats()
    print(f"\nStats:")
    print(f"  Size: {stats['total_size_mb']:.2f}MB")
    print(f"  Files: {stats['file_count']}")
    
    # Cleanup
    temp_mgr.cleanup_all()
    print("\nCleaned up all temp files")
    
    print("=" * 50)
