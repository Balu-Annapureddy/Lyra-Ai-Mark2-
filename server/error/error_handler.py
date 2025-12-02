"""
Standardized Error Handler
Provides consistent error responses across the application
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from .error_codes import ErrorCode

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    status: str = "error"
    code: str
    message: str
    details: Optional[str] = None
    severity: str = "error"
    timestamp: str
    http_status: int = 500


class LyraError(Exception):
    """Base exception for Lyra AI errors"""
    
    def __init__(self, code: ErrorCode, details: Optional[str] = None):
        self.code = code
        self.details = details
        super().__init__(f"{code}: {details}" if details else str(code))


class ErrorHandler:
    """Handles error code loading and response generation"""
    
    def __init__(self, error_codes_path: Path):
        self.error_codes_path = error_codes_path
        self.error_definitions: Dict[str, Dict[str, Any]] = {}
        self._load_error_codes()
    
    def _load_error_codes(self) -> None:
        """Load error code definitions from YAML"""
        try:
            with open(self.error_codes_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Remove config_version from definitions
            if 'config_version' in data:
                del data['config_version']
            
            self.error_definitions = data
            logger.info(f"Loaded {len(self.error_definitions)} error code definitions")
            
        except Exception as e:
            logger.error(f"Failed to load error codes: {e}")
            # Use minimal fallback definitions
            self.error_definitions = {
                "UNKNOWN_ERROR": {
                    "message": "An unknown error occurred",
                    "severity": "error",
                    "http_status": 500
                }
            }
    
    def create_error_response(
        self, 
        code: ErrorCode, 
        details: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> ErrorResponse:
        """
        Create a standardized error response
        
        Args:
            code: Error code enum
            details: Additional details about the error
            custom_message: Override the default message
            
        Returns:
            ErrorResponse object
        """
        code_str = code.value if isinstance(code, ErrorCode) else str(code)
        
        # Get error definition
        error_def = self.error_definitions.get(code_str, {
            "message": "Unknown error",
            "severity": "error",
            "http_status": 500
        })
        
        return ErrorResponse(
            code=code_str,
            message=custom_message or error_def.get("message", "Unknown error"),
            details=details,
            severity=error_def.get("severity", "error"),
            timestamp=datetime.utcnow().isoformat() + "Z",
            http_status=error_def.get("http_status", 500)
        )
    
    def get_http_status(self, code: ErrorCode) -> int:
        """Get HTTP status code for an error"""
        code_str = code.value if isinstance(code, ErrorCode) else str(code)
        error_def = self.error_definitions.get(code_str, {})
        return error_def.get("http_status", 500)
    
    def get_severity(self, code: ErrorCode) -> str:
        """Get severity level for an error"""
        code_str = code.value if isinstance(code, ErrorCode) else str(code)
        error_def = self.error_definitions.get(code_str, {})
        return error_def.get("severity", "error")
    
    def is_critical(self, code: ErrorCode) -> bool:
        """Check if an error is critical"""
        return self.get_severity(code) == "critical"


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler(error_codes_path: Optional[Path] = None) -> ErrorHandler:
    """Get or create the global error handler"""
    global _error_handler
    
    if _error_handler is None:
        if error_codes_path is None:
            # Default path
            error_codes_path = Path(__file__).parent / "error_codes.yaml"
        _error_handler = ErrorHandler(error_codes_path)
    
    return _error_handler


def create_error_response(code: ErrorCode, details: Optional[str] = None) -> ErrorResponse:
    """Convenience function to create error responses"""
    handler = get_error_handler()
    return handler.create_error_response(code, details)
