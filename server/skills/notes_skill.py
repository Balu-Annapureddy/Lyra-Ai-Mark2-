"""
Notes Skill - Quick Notes and Todos
"""

from typing import Dict, Any
import json
from pathlib import Path
from datetime import datetime
import logging

from skills.base_skill import BaseSkill
from core.paths import get_data_dir

logger = logging.getLogger(__name__)


class NotesSkill(BaseSkill):
    """Skill for quick notes and todos"""
    
    def __init__(self):
        super().__init__()
        self.notes_file = get_data_dir() / "notes.json"
        self._ensure_file_exists()
    
    @property
    def name(self) -> str:
        return "notes"
    
    @property
    def description(self) -> str:
        return "Create, list, and manage quick notes"
    
    @property
    def required_ram_mb(self) -> int:
        return 50
    
    def _ensure_file_exists(self):
        """Ensure notes file exists"""
        if not self.notes_file.exists():
            self.notes_file.write_text("[]", encoding='utf-8')
    
    def _load_notes(self) -> list:
        """Load notes from file"""
        try:
            return json.loads(self.notes_file.read_text(encoding='utf-8'))
        except:
            return []
    
    def _save_notes(self, notes: list):
        """Save notes to file"""
        self.notes_file.write_text(
            json.dumps(notes, indent=2),
            encoding='utf-8'
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute notes operation
        
        Params:
            action: "create", "list", "delete", "search"
            content: Note content (for create)
            tags: Note tags (for create, optional)
            id: Note ID (for delete)
            query: Search query (for search)
        
        Returns:
            Result with note data or operation status
        """
        try:
            action = params.get("action", "list")
            
            if action == "create":
                content = params.get("content", "")
                if not content:
                    return self._error_response("No content provided")
                
                tags = params.get("tags", [])
                
                # Create note
                notes = self._load_notes()
                note_id = len(notes) + 1
                
                note = {
                    "id": note_id,
                    "content": content,
                    "tags": tags,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                notes.append(note)
                self._save_notes(notes)
                
                logger.info(f"Created note: {note_id}")
                
                return self._success_response({
                    "action": "create",
                    "note": note
                })
            
            elif action == "list":
                notes = self._load_notes()
                
                # Sort by created_at (newest first)
                notes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                
                logger.info(f"Listed {len(notes)} notes")
                
                return self._success_response({
                    "action": "list",
                    "notes": notes,
                    "count": len(notes)
                })
            
            elif action == "delete":
                note_id = params.get("id")
                if not note_id:
                    return self._error_response("No note ID provided")
                
                notes = self._load_notes()
                notes = [n for n in notes if n["id"] != note_id]
                self._save_notes(notes)
                
                logger.info(f"Deleted note: {note_id}")
                
                return self._success_response({
                    "action": "delete",
                    "id": note_id
                })
            
            elif action == "search":
                query = params.get("query", "").lower()
                if not query:
                    return self._error_response("No search query provided")
                
                notes = self._load_notes()
                
                # Search in content and tags
                results = []
                for note in notes:
                    content = note.get("content", "").lower()
                    tags = [t.lower() for t in note.get("tags", [])]
                    
                    if query in content or any(query in tag for tag in tags):
                        results.append(note)
                
                logger.info(f"Search '{query}' found {len(results)} notes")
                
                return self._success_response({
                    "action": "search",
                    "query": query,
                    "results": results,
                    "count": len(results)
                })
            
            else:
                return self._error_response(f"Unknown action: {action}")
        
        except Exception as e:
            logger.error(f"Notes operation failed: {e}")
            return self._error_response(str(e))
