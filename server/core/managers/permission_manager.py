"""
Permission Manager - RBAC System
Manages user permissions with request/grant/revoke functionality
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Set
from datetime import datetime

from core.managers.config_manager import ConfigManager
from error.error_handler import ErrorHandler, LyraError
from error.error_codes import ErrorCode

logger = logging.getLogger(__name__)


class PermissionManager:
    """
    Manages user permissions for sensitive operations
    
    Permissions:
    - microphone: Access microphone for STT
    - camera: Access camera for vision
    - clipboard_read: Read clipboard content
    - clipboard_write: Write to clipboard
    - web_browse: Browse web/make HTTP requests
    - file_read: Read files from disk
    - file_write: Write files to disk
    """
    
    VALID_PERMISSIONS: Set[str] = {
        "microphone",
        "camera",
        "clipboard_read",
        "clipboard_write",
        "web_browse",
        "file_read",
        "file_write",
    }
    
    def __init__(self, config_manager: ConfigManager, error_handler: ErrorHandler):
        """
        Initialize permission manager
        
        Args:
            config_manager: ConfigManager instance for loading/saving permissions
            error_handler: ErrorHandler instance for error responses
        """
        self.config_manager = config_manager
        self.error_handler = error_handler
        self.permissions: Dict[str, bool] = {}
        self._load_permissions()
    
    def _load_permissions(self) -> None:
        """Load permissions from config file"""
        try:
            config = self.config_manager.load_json("permissions.json", required=False)
            
            if config is None:
                # Create default permissions (all denied)
                self.permissions = {perm: False for perm in self.VALID_PERMISSIONS}
                self._save_permissions()
                logger.info("Created default permissions (all denied)")
            else:
                # Remove config_version from permissions dict
                self.permissions = {
                    k: v for k, v in config.items() 
                    if k != "config_version"
                }
                logger.info(f"Loaded {len(self.permissions)} permissions from config")
        
        except Exception as e:
            logger.error(f"Failed to load permissions: {e}")
            # Fallback to all denied
            self.permissions = {perm: False for perm in self.VALID_PERMISSIONS}
    
    def _save_permissions(self) -> None:
        """Save permissions to config file"""
        try:
            config = {
                "config_version": "1.0",
                **self.permissions
            }
            self.config_manager.save_json("permissions.json", config)
            logger.info("Saved permissions to config")
        
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if a permission is granted
        
        Args:
            permission: Permission name to check
            
        Returns:
            True if permission is granted, False otherwise
        """
        if permission not in self.VALID_PERMISSIONS:
            logger.warning(f"Invalid permission requested: {permission}")
            return False
        
        return self.permissions.get(permission, False)
    
    def grant_permission(self, permission: str) -> None:
        """
        Grant a permission
        
        Args:
            permission: Permission name to grant
            
        Raises:
            ValueError: If permission name is invalid
        """
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}")
        
        self.permissions[permission] = True
        self._save_permissions()
        logger.info(f"Granted permission: {permission}")
    
    def revoke_permission(self, permission: str) -> None:
        """
        Revoke a permission
        
        Args:
            permission: Permission name to revoke
            
        Raises:
            ValueError: If permission name is invalid
        """
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}")
        
        self.permissions[permission] = False
        self._save_permissions()
        logger.info(f"Revoked permission: {permission}")
    
    def request_permission(self, permission: str, reason: Optional[str] = None) -> bool:
        """
        Request a permission (for future UI integration)
        Currently just checks if permission is granted
        
        Args:
            permission: Permission name to request
            reason: Optional reason for requesting permission
            
        Returns:
            True if permission is granted, False otherwise
        """
        if permission not in self.VALID_PERMISSIONS:
            logger.warning(f"Invalid permission requested: {permission}")
            return False
        
        has_perm = self.has_permission(permission)
        
        if not has_perm:
            logger.warning(
                f"Permission denied: {permission}" + 
                (f" (reason: {reason})" if reason else "")
            )
        
        return has_perm
    
    def get_all_permissions(self) -> Dict[str, bool]:
        """
        Get all permission states
        
        Returns:
            Dictionary of permission name to granted state
        """
        return self.permissions.copy()
    
    def get_granted_permissions(self) -> Set[str]:
        """
        Get set of granted permissions
        
        Returns:
            Set of permission names that are granted
        """
        return {perm for perm, granted in self.permissions.items() if granted}
    
    def get_denied_permissions(self) -> Set[str]:
        """
        Get set of denied permissions
        
        Returns:
            Set of permission names that are denied
        """
        return {perm for perm, granted in self.permissions.items() if not granted}
    
    def check_permission_or_raise(self, permission: str, reason: Optional[str] = None) -> None:
        """
        Check permission and raise error if denied
        
        Args:
            permission: Permission name to check
            reason: Optional reason for requiring permission
            
        Raises:
            LyraError: If permission is denied
        """
        if not self.has_permission(permission):
            details = f"Permission '{permission}' is required"
            if reason:
                details += f": {reason}"
            raise LyraError(ErrorCode.PERMISSION_DENIED, details)
    
    def health_check(self) -> Dict[str, any]:
        """
        Health check for permission manager
        
        Returns:
            Dictionary with health status
        """
        return {
            "status": "ok",
            "permissions_loaded": len(self.permissions),
            "granted_count": len(self.get_granted_permissions()),
            "denied_count": len(self.get_denied_permissions()),
        }


# Singleton instance management
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager(
    config_manager: Optional[ConfigManager] = None,
    error_handler: Optional[ErrorHandler] = None
) -> PermissionManager:
    """
    Get or create the global permission manager
    
    Args:
        config_manager: ConfigManager instance (required for first call)
        error_handler: ErrorHandler instance (required for first call)
        
    Returns:
        PermissionManager instance
    """
    global _permission_manager
    
    if _permission_manager is None:
        if config_manager is None or error_handler is None:
            raise ValueError("config_manager and error_handler required for first call")
        _permission_manager = PermissionManager(config_manager, error_handler)
    
    return _permission_manager
