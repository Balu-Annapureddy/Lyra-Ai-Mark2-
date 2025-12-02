"""
Base Skill - Abstract Base Class for All Skills
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import platform
import psutil
import logging

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """
    Abstract base class for all skills
    
    Each skill must implement:
    - name: Unique skill identifier
    - description: What the skill does
    - required_ram_mb: RAM required to run
    - platforms: Supported platforms
    - can_execute(): Check if skill can run
    - execute(): Run the skill
    """
    
    def __init__(self):
        """Initialize base skill"""
        self._validate_implementation()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique skill name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Skill description"""
        pass
    
    @property
    def required_ram_mb(self) -> int:
        """RAM required in MB (default: 100MB)"""
        return 100
    
    @property
    def platforms(self) -> List[str]:
        """Supported platforms (default: all)"""
        return ["windows", "linux", "darwin"]  # darwin = macOS
    
    @property
    def requires_internet(self) -> bool:
        """Whether skill requires internet (default: False)"""
        return False
    
    def _validate_implementation(self):
        """Validate that subclass implements required methods"""
        required_attrs = ['name', 'description']
        for attr in required_attrs:
            if not hasattr(self, attr):
                raise NotImplementedError(
                    f"Skill must implement '{attr}' property"
                )
    
    def can_execute(self) -> tuple[bool, Optional[str]]:
        """
        Check if skill can execute
        
        Returns:
            (can_execute, reason_if_not)
        """
        # Check platform compatibility
        current_platform = platform.system().lower()
        if current_platform not in self.platforms:
            return False, f"Platform {current_platform} not supported"
        
        # Check RAM availability
        available_ram_mb = psutil.virtual_memory().available / (1024 ** 2)
        if available_ram_mb < self.required_ram_mb:
            return False, f"Insufficient RAM: need {self.required_ram_mb}MB, have {available_ram_mb:.0f}MB"
        
        # Check RAM usage percentage
        ram_percent = psutil.virtual_memory().percent
        if ram_percent > 90:
            return False, f"RAM usage too high: {ram_percent:.1f}%"
        
        return True, None
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill
        
        Args:
            params: Skill parameters
        
        Returns:
            Result dictionary with:
            - success: bool
            - data: Any result data
            - error: Optional error message
        """
        pass
    
    def _success_response(self, data: Any) -> Dict[str, Any]:
        """Create success response"""
        return {
            "success": True,
            "data": data,
            "error": None
        }
    
    def _error_response(self, error: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "data": None,
            "error": error
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get skill information"""
        can_run, reason = self.can_execute()
        
        return {
            "name": self.name,
            "description": self.description,
            "required_ram_mb": self.required_ram_mb,
            "platforms": self.platforms,
            "requires_internet": self.requires_internet,
            "can_execute": can_run,
            "reason": reason
        }


if __name__ == "__main__":
    # Test base skill
    class TestSkill(BaseSkill):
        @property
        def name(self) -> str:
            return "test_skill"
        
        @property
        def description(self) -> str:
            return "A test skill"
        
        async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
            return self._success_response({"message": "Test executed"})
    
    skill = TestSkill()
    print("Skill Info:")
    print(skill.get_info())
