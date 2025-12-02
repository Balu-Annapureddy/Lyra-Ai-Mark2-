"""
Permission Manager Enhancements
Adds event system, backup/restore, dry-run mode, and structured logging
"""

from typing import Callable, List, Optional
from pathlib import Path
import json
from datetime import datetime

from core.permission_events import PermissionEvent, PermissionEventType
from core.events import get_event_bus, EventType
from core.structured_logger import get_structured_logger


class PermissionManagerEnhancements:
    """
    Mixin class for Permission Manager enhancements
    Add these methods to PermissionManager class
    """
    
    def __init_enhancements__(self, dry_run: bool = False):
        """Initialize enhancements"""
        self.dry_run = dry_run
        self.event_bus = get_event_bus()
        self.struct_logger = get_structured_logger("PermissionManager")
        self._event_listeners: List[Callable] = []
    
    def add_event_listener(self, listener: Callable[[PermissionEvent], None]):
        """
        Add a listener for permission events
        
        Args:
            listener: Callback function that receives PermissionEvent
        """
        self._event_listeners.append(listener)
        self.struct_logger.info(
            "listener_added",
            "Permission event listener added",
            listener_count=len(self._event_listeners)
        )
    
    def remove_event_listener(self, listener: Callable):
        """Remove an event listener"""
        if listener in self._event_listeners:
            self._event_listeners.remove(listener)
            self.struct_logger.info(
                "listener_removed",
                "Permission event listener removed"
            )
    
    def _fire_event(self, event: PermissionEvent):
        """Fire a permission event to all listeners"""
        # Publish to event bus
        self.event_bus.publish_sync(
            EventType.PERMISSION_CHANGED,
            event.to_dict(),
            source="permission_manager"
        )
        
        # Call all listeners
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception as e:
                self.struct_logger.error(
                    "listener_error",
                    f"Error in event listener: {e}",
                    permission=event.permission
                )
    
    def grant_permission_enhanced(self, permission: str, reason: Optional[str] = None):
        """
        Grant permission with event firing
        
        Args:
            permission: Permission name
            reason: Optional reason for granting
        """
        if self.dry_run:
            self.struct_logger.info(
                "dry_run_grant",
                f"[DRY RUN] Would grant permission: {permission}",
                permission=permission,
                reason=reason
            )
            return
        
        # Original grant logic
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}")
        
        self.permissions[permission] = True
        self._save_permissions()
        
        # Fire event
        event = PermissionEvent.create(
            PermissionEventType.GRANTED,
            permission,
            reason=reason
        )
        self._fire_event(event)
        
        self.struct_logger.info(
            "permission_granted",
            f"Permission granted: {permission}",
            permission=permission,
            reason=reason
        )
    
    def revoke_permission_enhanced(self, permission: str, reason: Optional[str] = None):
        """
        Revoke permission with event firing
        
        Args:
            permission: Permission name
            reason: Optional reason for revoking
        """
        if self.dry_run:
            self.struct_logger.info(
                "dry_run_revoke",
                f"[DRY RUN] Would revoke permission: {permission}",
                permission=permission,
                reason=reason
            )
            return
        
        if permission not in self.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}")
        
        self.permissions[permission] = False
        self._save_permissions()
        
        # Fire event
        event = PermissionEvent.create(
            PermissionEventType.REVOKED,
            permission,
            reason=reason
        )
        self._fire_event(event)
        
        self.struct_logger.info(
            "permission_revoked",
            f"Permission revoked: {permission}",
            permission=permission,
            reason=reason
        )
    
    def freeze_state(self, backup_name: Optional[str] = None) -> Path:
        """
        Export current permissions to a backup file
        
        Args:
            backup_name: Optional backup file name
            
        Returns:
            Path to backup file
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"permissions_backup_{timestamp}.json"
        
        backup_dir = self.config_manager.config_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / backup_name
        
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "permissions": self.permissions.copy(),
            "config_version": "1.0"
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        self.struct_logger.info(
            "state_frozen",
            f"Permissions backed up to {backup_path}",
            backup_path=str(backup_path),
            permission_count=len(self.permissions)
        )
        
        return backup_path
    
    def restore_state(self, backup_path: Path) -> bool:
        """
        Restore permissions from a backup file
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            if 'permissions' not in backup_data:
                self.struct_logger.error(
                    "restore_failed",
                    "Invalid backup file: missing permissions",
                    backup_path=str(backup_path)
                )
                return False
            
            if self.dry_run:
                self.struct_logger.info(
                    "dry_run_restore",
                    f"[DRY RUN] Would restore {len(backup_data['permissions'])} permissions",
                    backup_path=str(backup_path)
                )
                return True
            
            # Restore permissions
            self.permissions = backup_data['permissions']
            self._save_permissions()
            
            self.struct_logger.info(
                "state_restored",
                f"Permissions restored from {backup_path}",
                backup_path=str(backup_path),
                backup_timestamp=backup_data.get('timestamp'),
                permission_count=len(self.permissions)
            )
            
            return True
            
        except Exception as e:
            self.struct_logger.error(
                "restore_failed",
                f"Failed to restore permissions: {e}",
                backup_path=str(backup_path),
                error=str(e)
            )
            return False
    
    def list_backups(self) -> List[Path]:
        """
        List all permission backup files
        
        Returns:
            List of backup file paths
        """
        backup_dir = self.config_manager.config_dir / "backups"
        if not backup_dir.exists():
            return []
        
        backups = list(backup_dir.glob("permissions_backup_*.json"))
        backups.sort(reverse=True)  # Most recent first
        
        return backups
