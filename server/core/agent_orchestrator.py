"""
Agent Orchestrator - Central Intelligence System
Coordinates skills, memory, intent parsing, and multi-step reasoning
Integrates with all safety and resource management systems
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from core.ram_guard import check_ram_before_task, ModelType
from core.safety import safe_model_operation, with_async_timeout
from core.lazy_loader import get_lazy_loader
from core.warmup import get_warmer
from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """User intent types"""
    CHAT = "chat"  # Simple conversation
    TASK = "task"  # Execute a task/skill
    QUESTION = "question"  # Answer a question
    COMMAND = "command"  # System command
    UNKNOWN = "unknown"


class AgentOrchestrator:
    """
    Central intelligence that coordinates all AI components
    - Intent parsing
    - Skill selection and execution
    - Memory integration
    - Multi-step reasoning
    - Safety checks
    """
    
    def __init__(self):
        """Initialize agent orchestrator"""
        self.lazy_loader = get_lazy_loader()
        self.warmer = get_warmer()
        self.skills: Dict[str, BaseSkill] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_history_length = 50
        
        logger.info("AgentOrchestrator initialized")
    
    def register_skill(self, skill: BaseSkill):
        """
        Register a skill with the orchestrator
        
        Args:
            skill: Skill instance
        """
        self.skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name}")
    
    def register_skills(self, skills: List[BaseSkill]):
        """Register multiple skills"""
        for skill in skills:
            self.register_skill(skill)
    
    async def process_message(
        self,
        message: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message with full orchestration
        
        Args:
            message: User message
            user_id: User identifier
            context: Optional context dictionary
        
        Returns:
            Response dictionary with:
            - response: str
            - intent: IntentType
            - skill_used: Optional[str]
            - metadata: Dict
        """
        logger.info(f"Processing message: {message[:50]}...")
        
        # Add to conversation history
        self._add_to_history({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Parse intent
        intent = await self._parse_intent(message)
        logger.info(f"Detected intent: {intent}")
        
        # Route based on intent
        if intent == IntentType.TASK:
            response = await self._handle_task(message, context)
        elif intent == IntentType.COMMAND:
            response = await self._handle_command(message, context)
        elif intent == IntentType.QUESTION:
            response = await self._handle_question(message, context)
        else:  # CHAT or UNKNOWN
            response = await self._handle_chat(message, context)
        
        # Add response to history
        self._add_to_history({
            "role": "assistant",
            "content": response.get("response", ""),
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "skill_used": response.get("skill_used")
        })
        
        return response
    
    async def _parse_intent(self, message: str) -> IntentType:
        """
        Parse user intent from message
        
        Args:
            message: User message
        
        Returns:
            Detected intent type
        """
        message_lower = message.lower()
        
        # Task keywords
        task_keywords = [
            "copy", "paste", "open", "search", "remind", "note",
            "create", "delete", "list", "read", "write"
        ]
        if any(keyword in message_lower for keyword in task_keywords):
            return IntentType.TASK
        
        # Command keywords
        command_keywords = [
            "settings", "config", "status", "help", "exit", "quit"
        ]
        if any(keyword in message_lower for keyword in command_keywords):
            return IntentType.COMMAND
        
        # Question keywords
        question_keywords = ["what", "how", "why", "when", "where", "who", "?"]
        if any(keyword in message_lower for keyword in question_keywords):
            return IntentType.QUESTION
        
        # Default to chat
        return IntentType.CHAT
    
    async def _handle_task(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle task execution"""
        # Select appropriate skill
        skill_name = await self._select_skill(message)
        
        if not skill_name or skill_name not in self.skills:
            return {
                "response": "I'm not sure how to help with that task.",
                "intent": IntentType.TASK,
                "skill_used": None,
                "metadata": {"error": "No suitable skill found"}
            }
        
        skill = self.skills[skill_name]
        
        # Check if skill can execute
        can_execute, reason = skill.can_execute()
        if not can_execute:
            return {
                "response": f"Cannot execute task: {reason}",
                "intent": IntentType.TASK,
                "skill_used": skill_name,
                "metadata": {"error": reason}
            }
        
        # Extract parameters from message
        params = await self._extract_skill_params(message, skill_name)
        
        # Execute skill with safety wrapper
        try:
            result = await safe_model_operation(
                lambda: skill.execute(params),
                timeout=30,
                operation_name=f"skill_{skill_name}"
            )
            
            if result.get("success"):
                return {
                    "response": self._format_skill_response(result, skill_name),
                    "intent": IntentType.TASK,
                    "skill_used": skill_name,
                    "metadata": result.get("data", {})
                }
            else:
                return {
                    "response": f"Task failed: {result.get('error', 'Unknown error')}",
                    "intent": IntentType.TASK,
                    "skill_used": skill_name,
                    "metadata": {"error": result.get("error")}
                }
        
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            return {
                "response": f"An error occurred: {str(e)}",
                "intent": IntentType.TASK,
                "skill_used": skill_name,
                "metadata": {"error": str(e)}
            }
    
    async def _select_skill(self, message: str) -> Optional[str]:
        """Select appropriate skill for message"""
        message_lower = message.lower()
        
        # Simple keyword-based selection
        skill_keywords = {
            "clipboard": ["copy", "paste", "clipboard"],
            "browser": ["open", "search", "browse", "url", "website"],
            "file": ["read", "write", "file", "save", "load"],
            "scheduling": ["remind", "reminder", "schedule", "calendar"],
            "notes": ["note", "notes", "write down", "remember"]
        }
        
        for skill_name, keywords in skill_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return skill_name
        
        return None
    
    async def _extract_skill_params(
        self,
        message: str,
        skill_name: str
    ) -> Dict[str, Any]:
        """Extract parameters for skill from message"""
        # Simplified parameter extraction
        # In production, use LLM for better extraction
        
        params = {}
        message_lower = message.lower()
        
        if skill_name == "clipboard":
            if "copy" in message_lower:
                params["action"] = "copy"
                # Extract text after "copy"
                if "copy " in message_lower:
                    text = message.split("copy ", 1)[1]
                    params["text"] = text
            else:
                params["action"] = "paste"
        
        elif skill_name == "browser":
            if "search" in message_lower:
                params["action"] = "search"
                # Extract query
                if "search for " in message_lower:
                    query = message.split("search for ", 1)[1]
                    params["query"] = query
                elif "search " in message_lower:
                    query = message.split("search ", 1)[1]
                    params["query"] = query
            else:
                params["action"] = "open"
                # Extract URL
                words = message.split()
                for word in words:
                    if "." in word or "http" in word:
                        params["url"] = word
                        break
        
        elif skill_name == "file":
            if "read" in message_lower:
                params["action"] = "read"
            elif "write" in message_lower:
                params["action"] = "write"
            else:
                params["action"] = "list"
            
            # Extract path
            words = message.split()
            for word in words:
                if "/" in word or "\\" in word or "." in word:
                    params["path"] = word
                    break
        
        return params
    
    def _format_skill_response(
        self,
        result: Dict[str, Any],
        skill_name: str
    ) -> str:
        """Format skill result into natural language response"""
        data = result.get("data", {})
        
        if skill_name == "clipboard":
            action = data.get("action")
            if action == "copy":
                return f"Copied {data.get('length', 0)} characters to clipboard."
            else:
                return f"Pasted: {data.get('content', '')}"
        
        elif skill_name == "browser":
            action = data.get("action")
            if action == "search":
                return f"Searched for '{data.get('query')}' on {data.get('engine', 'Google')}."
            else:
                return f"Opened {data.get('url')}."
        
        elif skill_name == "file":
            action = data.get("action")
            if action == "read":
                return f"Read file ({data.get('size_bytes', 0)} bytes):\n{data.get('content', '')[:200]}"
            elif action == "write":
                return f"Wrote {data.get('size_bytes', 0)} bytes to file."
            else:
                return f"Found {data.get('count', 0)} items."
        
        return "Task completed successfully."
    
    async def _handle_command(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle system commands"""
        message_lower = message.lower()
        
        if "status" in message_lower:
            status = self._get_system_status()
            return {
                "response": self._format_status(status),
                "intent": IntentType.COMMAND,
                "skill_used": None,
                "metadata": status
            }
        
        elif "help" in message_lower:
            return {
                "response": self._get_help_text(),
                "intent": IntentType.COMMAND,
                "skill_used": None,
                "metadata": {}
            }
        
        return {
            "response": "Unknown command.",
            "intent": IntentType.COMMAND,
            "skill_used": None,
            "metadata": {}
        }
    
    async def _handle_question(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle questions (would use LLM in production)"""
        return {
            "response": "I can help you with tasks like copying text, opening websites, managing files, and more. What would you like me to do?",
            "intent": IntentType.QUESTION,
            "skill_used": None,
            "metadata": {}
        }
    
    async def _handle_chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle general chat (would use LLM in production)"""
        return {
            "response": "Hello! I'm Lyra, your AI assistant. I can help you with various tasks. What would you like me to do?",
            "intent": IntentType.CHAT,
            "skill_used": None,
            "metadata": {}
        }
    
    def _add_to_history(self, entry: Dict[str, Any]):
        """Add entry to conversation history"""
        self.conversation_history.append(entry)
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "skills_registered": len(self.skills),
            "skills": list(self.skills.keys()),
            "conversation_length": len(self.conversation_history)
        }
    
    def _format_status(self, status: Dict[str, Any]) -> str:
        """Format status for display"""
        return f"""System Status:
- Skills: {status['skills_registered']} registered
- Available skills: {', '.join(status['skills'])}
- Conversation history: {status['conversation_length']} messages
"""
    
    def _get_help_text(self) -> str:
        """Get help text"""
        skills_text = "\n".join([
            f"  - {skill.name}: {skill.description}"
            for skill in self.skills.values()
        ])
        
        return f"""Lyra AI Assistant - Help

Available Skills:
{skills_text}

Commands:
  - status: Show system status
  - help: Show this help message

Examples:
  - "Copy this text to clipboard"
  - "Search for Python tutorials"
  - "Open google.com"
  - "Read file.txt"
"""
    
    def get_conversation_history(
        self,
        last_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        if last_n:
            return self.conversation_history[-last_n:]
        return self.conversation_history


# Global orchestrator instance
_global_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """Get global agent orchestrator instance"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = AgentOrchestrator()
    return _global_orchestrator


if __name__ == "__main__":
    # Test agent orchestrator
    import asyncio
    from skills.clipboard_skill import ClipboardSkill
    from skills.browser_skill import BrowserSkill
    
    async def test():
        print("Testing Agent Orchestrator")
        print("=" * 50)
        
        orchestrator = AgentOrchestrator()
        
        # Register skills
        orchestrator.register_skills([
            ClipboardSkill(),
            BrowserSkill()
        ])
        
        # Test messages
        messages = [
            "Copy hello world",
            "Search for Python tutorials",
            "What can you do?",
            "status"
        ]
        
        for msg in messages:
            print(f"\nUser: {msg}")
            response = await orchestrator.process_message(msg)
            print(f"Lyra: {response['response']}")
            print(f"Intent: {response['intent']}, Skill: {response.get('skill_used')}")
        
        print("=" * 50)
    
    asyncio.run(test())
