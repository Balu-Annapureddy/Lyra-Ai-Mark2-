"""
Scheduling Skill - Reminders and Calendar Events
"""

from typing import Dict, Any
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

from skills.base_skill import BaseSkill
from core.paths import get_data_dir

logger = logging.getLogger(__name__)


class SchedulingSkill(BaseSkill):
    """Skill for reminders and scheduling"""
    
    def __init__(self):
        super().__init__()
        self.reminders_file = get_data_dir() / "reminders.json"
        self._ensure_file_exists()
    
    @property
    def name(self) -> str:
        return "scheduling"
    
    @property
    def description(self) -> str:
        return "Create, list, and manage reminders"
    
    @property
    def required_ram_mb(self) -> int:
        return 50
    
    def _ensure_file_exists(self):
        """Ensure reminders file exists"""
        if not self.reminders_file.exists():
            self.reminders_file.write_text("[]", encoding='utf-8')
    
    def _load_reminders(self) -> list:
        """Load reminders from file"""
        try:
            return json.loads(self.reminders_file.read_text(encoding='utf-8'))
        except:
            return []
    
    def _save_reminders(self, reminders: list):
        """Save reminders to file"""
        self.reminders_file.write_text(
            json.dumps(reminders, indent=2),
            encoding='utf-8'
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scheduling operation
        
        Params:
            action: "create", "list", "delete", or "complete"
            title: Reminder title (for create)
            time: Reminder time (for create, format: "YYYY-MM-DD HH:MM")
            id: Reminder ID (for delete/complete)
        
        Returns:
            Result with reminder data or operation status
        """
        try:
            action = params.get("action", "list")
            
            if action == "create":
                title = params.get("title", "")
                if not title:
                    return self._error_response("No title provided")
                
                time_str = params.get("time", "")
                if not time_str:
                    return self._error_response("No time provided")
                
                # Parse time
                try:
                    reminder_time = datetime.fromisoformat(time_str)
                except:
                    return self._error_response(f"Invalid time format: {time_str}")
                
                # Create reminder
                reminders = self._load_reminders()
                reminder_id = len(reminders) + 1
                
                reminder = {
                    "id": reminder_id,
                    "title": title,
                    "time": reminder_time.isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "completed": False
                }
                
                reminders.append(reminder)
                self._save_reminders(reminders)
                
                logger.info(f"Created reminder: {title} at {time_str}")
                
                return self._success_response({
                    "action": "create",
                    "reminder": reminder
                })
            
            elif action == "list":
                reminders = self._load_reminders()
                
                # Filter active reminders
                active = [r for r in reminders if not r.get("completed", False)]
                completed = [r for r in reminders if r.get("completed", False)]
                
                logger.info(f"Listed reminders: {len(active)} active, {len(completed)} completed")
                
                return self._success_response({
                    "action": "list",
                    "active": active,
                    "completed": completed,
                    "total": len(reminders)
                })
            
            elif action == "delete":
                reminder_id = params.get("id")
                if not reminder_id:
                    return self._error_response("No reminder ID provided")
                
                reminders = self._load_reminders()
                reminders = [r for r in reminders if r["id"] != reminder_id]
                self._save_reminders(reminders)
                
                logger.info(f"Deleted reminder: {reminder_id}")
                
                return self._success_response({
                    "action": "delete",
                    "id": reminder_id
                })
            
            elif action == "complete":
                reminder_id = params.get("id")
                if not reminder_id:
                    return self._error_response("No reminder ID provided")
                
                reminders = self._load_reminders()
                for reminder in reminders:
                    if reminder["id"] == reminder_id:
                        reminder["completed"] = True
                        reminder["completed_at"] = datetime.now().isoformat()
                
                self._save_reminders(reminders)
                
                logger.info(f"Completed reminder: {reminder_id}")
                
                return self._success_response({
                    "action": "complete",
                    "id": reminder_id
                })
            
            else:
                return self._error_response(f"Unknown action: {action}")
        
        except Exception as e:
            logger.error(f"Scheduling operation failed: {e}")
            return self._error_response(str(e))
