"""
Clipboard Skill - Copy and Paste Operations
"""

from typing import Dict, Any
import pyperclip
import logging

from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class ClipboardSkill(BaseSkill):
    """Skill for clipboard operations"""
    
    @property
    def name(self) -> str:
        return "clipboard"
    
    @property
    def description(self) -> str:
        return "Copy text to or paste text from clipboard"
    
    @property
    def required_ram_mb(self) -> int:
        return 50  # Very lightweight
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute clipboard operation
        
        Params:
            action: "copy" or "paste"
            text: Text to copy (for copy action)
        
        Returns:
            Result with clipboard content or success status
        """
        try:
            action = params.get("action", "paste")
            
            if action == "copy":
                text = params.get("text", "")
                if not text:
                    return self._error_response("No text provided to copy")
                
                pyperclip.copy(text)
                logger.info(f"Copied {len(text)} characters to clipboard")
                
                return self._success_response({
                    "action": "copy",
                    "length": len(text)
                })
            
            elif action == "paste":
                content = pyperclip.paste()
                logger.info(f"Pasted {len(content)} characters from clipboard")
                
                return self._success_response({
                    "action": "paste",
                    "content": content,
                    "length": len(content)
                })
            
            else:
                return self._error_response(f"Unknown action: {action}")
        
        except Exception as e:
            logger.error(f"Clipboard operation failed: {e}")
            return self._error_response(str(e))
