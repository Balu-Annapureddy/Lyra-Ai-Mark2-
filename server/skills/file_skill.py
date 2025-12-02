"""
File Skill - File Operations (Read, Write, List)
"""

from typing import Dict, Any
from pathlib import Path
import logging

from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class FileSkill(BaseSkill):
    """Skill for file operations"""
    
    @property
    def name(self) -> str:
        return "file"
    
    @property
    def description(self) -> str:
        return "Read, write, and list files"
    
    @property
    def required_ram_mb(self) -> int:
        return 100
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file operation
        
        Params:
            action: "read", "write", or "list"
            path: File or directory path
            content: Content to write (for write action)
            max_size_mb: Max file size to read (default: 10MB)
        
        Returns:
            Result with file content or operation status
        """
        try:
            action = params.get("action", "read")
            path_str = params.get("path", "")
            
            if not path_str:
                return self._error_response("No path provided")
            
            path = Path(path_str).expanduser()
            
            if action == "read":
                if not path.exists():
                    return self._error_response(f"File not found: {path}")
                
                if not path.is_file():
                    return self._error_response(f"Not a file: {path}")
                
                # Check file size
                max_size_mb = params.get("max_size_mb", 10)
                size_mb = path.stat().st_size / (1024 ** 2)
                
                if size_mb > max_size_mb:
                    return self._error_response(
                        f"File too large: {size_mb:.1f}MB > {max_size_mb}MB"
                    )
                
                # Read file
                content = path.read_text(encoding='utf-8')
                logger.info(f"Read file: {path} ({len(content)} chars)")
                
                return self._success_response({
                    "action": "read",
                    "path": str(path),
                    "content": content,
                    "size_bytes": path.stat().st_size
                })
            
            elif action == "write":
                content = params.get("content", "")
                if not content:
                    return self._error_response("No content provided")
                
                # Create parent directories if needed
                path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                path.write_text(content, encoding='utf-8')
                logger.info(f"Wrote file: {path} ({len(content)} chars)")
                
                return self._success_response({
                    "action": "write",
                    "path": str(path),
                    "size_bytes": len(content.encode('utf-8'))
                })
            
            elif action == "list":
                if not path.exists():
                    return self._error_response(f"Directory not found: {path}")
                
                if not path.is_dir():
                    return self._error_response(f"Not a directory: {path}")
                
                # List directory contents
                items = []
                for item in path.iterdir():
                    items.append({
                        "name": item.name,
                        "type": "file" if item.is_file() else "directory",
                        "size_bytes": item.stat().st_size if item.is_file() else None
                    })
                
                logger.info(f"Listed directory: {path} ({len(items)} items)")
                
                return self._success_response({
                    "action": "list",
                    "path": str(path),
                    "items": items,
                    "count": len(items)
                })
            
            else:
                return self._error_response(f"Unknown action: {action}")
        
        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return self._error_response(str(e))
