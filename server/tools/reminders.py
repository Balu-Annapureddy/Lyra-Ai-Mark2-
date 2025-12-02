"""
Reminders Tool
Simple JSON-based reminder system
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ReminderManager:
    """
    Manage reminders with JSON persistence
    """
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.reminders_file = self.data_dir / "reminders.json"
        self.reminders = self._load_reminders()
    
    def _load_reminders(self) -> List[Dict]:
        """Load reminders from JSON file"""
        if self.reminders_file.exists():
            try:
                with open(self.reminders_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load reminders: {e}")
                return []
        return []
    
    def _save_reminders(self):
        """Save reminders to JSON file"""
        try:
            with open(self.reminders_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save reminders: {e}")
    
    def add_reminder(
        self,
        title: str,
        description: str = "",
        due_time: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict:
        """
        Add a new reminder
        
        Args:
            title: Reminder title
            description: Optional description
            due_time: ISO format datetime string
            priority: low/normal/high
        
        Returns:
            Created reminder dict
        """
        reminder = {
            "id": len(self.reminders) + 1,
            "title": title,
            "description": description,
            "due_time": due_time,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "completed": False
        }
        
        self.reminders.append(reminder)
        self._save_reminders()
        
        logger.info(f"Added reminder: {title}")
        return reminder
    
    def get_reminders(
        self,
        completed: Optional[bool] = None,
        priority: Optional[str] = None
    ) -> List[Dict]:
        """
        Get reminders with optional filtering
        
        Args:
            completed: Filter by completion status
            priority: Filter by priority
        
        Returns:
            List of matching reminders
        """
        results = self.reminders
        
        if completed is not None:
            results = [r for r in results if r["completed"] == completed]
        
        if priority:
            results = [r for r in results if r["priority"] == priority]
        
        return results
    
    def complete_reminder(self, reminder_id: int) -> bool:
        """
        Mark reminder as completed
        
        Args:
            reminder_id: ID of reminder to complete
        
        Returns:
            True if successful
        """
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["completed"] = True
                reminder["completed_at"] = datetime.now().isoformat()
                self._save_reminders()
                logger.info(f"Completed reminder: {reminder['title']}")
                return True
        
        return False
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """
        Delete a reminder
        
        Args:
            reminder_id: ID of reminder to delete
        
        Returns:
            True if successful
        """
        initial_count = len(self.reminders)
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
        
        if len(self.reminders) < initial_count:
            self._save_reminders()
            logger.info(f"Deleted reminder ID: {reminder_id}")
            return True
        
        return False
    
    def get_upcoming_reminders(self, hours: int = 24) -> List[Dict]:
        """
        Get reminders due in the next N hours
        
        Args:
            hours: Number of hours to look ahead
        
        Returns:
            List of upcoming reminders
        """
        # TODO: Implement time-based filtering
        # For now, return all incomplete reminders
        return self.get_reminders(completed=False)
