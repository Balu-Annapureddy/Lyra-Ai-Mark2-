"""
Permission Event System
Fires events when permissions change for UI notifications
"""

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


class PermissionEventType(Enum):
    """Types of permission events"""
    GRANTED = "granted"
    REVOKED = "revoked"
    REQUESTED = "requested"
    DENIED = "denied"


@dataclass
class PermissionEvent:
    """
    Permission event data
    
    Attributes:
        event_type: Type of event
        permission: Permission name
        timestamp: When the event occurred
        reason: Optional reason for the event
        user_id: Optional user ID (for multi-user systems)
        extras: Additional event data
    """
    event_type: PermissionEventType
    permission: str
    timestamp: str
    reason: Optional[str] = None
    user_id: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        return data
    
    @classmethod
    def create(
        cls,
        event_type: PermissionEventType,
        permission: str,
        reason: Optional[str] = None,
        user_id: Optional[str] = None,
        **extras
    ) -> "PermissionEvent":
        """
        Create a permission event
        
        Args:
            event_type: Type of event
            permission: Permission name
            reason: Optional reason
            user_id: Optional user ID
            **extras: Additional event data
            
        Returns:
            PermissionEvent instance
        """
        return cls(
            event_type=event_type,
            permission=permission,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            user_id=user_id,
            extras=extras if extras else None
        )
