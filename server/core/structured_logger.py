"""
Structured Logging Utility
Provides consistent logging format across all managers
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime


class StructuredLogger:
    """
    Structured logger for consistent logging format
    
    Format: { component, status, event, message, timestamp, extras }
    """
    
    def __init__(self, component: str):
        """
        Initialize structured logger
        
        Args:
            component: Component name (e.g., "PermissionManager")
        """
        self.component = component
        self.logger = logging.getLogger(component)
    
    def _format_log(
        self,
        status: str,
        event: str,
        message: str,
        **extras
    ) -> str:
        """Format log message as structured JSON"""
        log_data = {
            "component": self.component,
            "status": status,
            "event": event,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add any extra fields
        if extras:
            log_data["extras"] = extras
        
        return json.dumps(log_data)
    
    def info(self, event: str, message: str, **extras):
        """Log info level message"""
        log_msg = self._format_log("info", event, message, **extras)
        self.logger.info(log_msg)
    
    def warning(self, event: str, message: str, **extras):
        """Log warning level message"""
        log_msg = self._format_log("warning", event, message, **extras)
        self.logger.warning(log_msg)
    
    def error(self, event: str, message: str, **extras):
        """Log error level message"""
        log_msg = self._format_log("error", event, message, **extras)
        self.logger.error(log_msg)
    
    def debug(self, event: str, message: str, **extras):
        """Log debug level message"""
        log_msg = self._format_log("debug", event, message, **extras)
        self.logger.debug(log_msg)
    
    def critical(self, event: str, message: str, **extras):
        """Log critical level message"""
        log_msg = self._format_log("critical", event, message, **extras)
        self.logger.critical(log_msg)


def get_structured_logger(component: str) -> StructuredLogger:
    """
    Get a structured logger for a component
    
    Args:
        component: Component name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(component)
