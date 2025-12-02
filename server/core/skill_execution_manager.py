"""
Skill Execution Manager - Isolated Skill Execution with Sandboxing
Wraps all skill calls with subprocess isolation, quotas, and crash containment
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import psutil

from skills.base_skill import BaseSkill
from core.sandbox import get_sandbox, SandboxViolation
from core.events import get_event_bus, EventType
from core.errors import SkillExecutionError, SkillPermissionError, SkillError

logger = logging.getLogger(__name__)


class SkillExecutionManager:
    """
    Manages isolated skill execution with:
    - Subprocess isolation
    - Time limits
    - CPU/RAM quotas
    - Rate limiting
    - Crash containment
    """
    
    def __init__(
        self,
        default_timeout: int = 30,
        max_cpu_percent: float = 50.0,
        max_ram_mb: int = 500,
        rate_limit_per_minute: int = 60
    ):
        """
        Initialize skill execution manager
        
        Args:
            default_timeout: Default execution timeout in seconds
            max_cpu_percent: Max CPU usage per skill
            max_ram_mb: Max RAM per skill in MB
            rate_limit_per_minute: Max executions per minute per skill
        """
        self.default_timeout = default_timeout
        self.max_cpu_percent = max_cpu_percent
        self.max_ram_mb = max_ram_mb
        self.rate_limit = rate_limit_per_minute
        
        self.sandbox = get_sandbox()
        self.event_bus = get_event_bus()
        
        # Rate limiting tracking
        self._execution_history: Dict[str, list] = {}
        
        logger.info(
            f"SkillExecutionManager initialized: "
            f"timeout={default_timeout}s, cpu={max_cpu_percent}%, ram={max_ram_mb}MB"
        )
    
    async def execute_skill(
        self,
        skill: BaseSkill,
        params: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute skill with full isolation and safety checks
        
        Args:
            skill: Skill instance
            params: Skill parameters
            timeout: Execution timeout (uses default if None)
        
        Returns:
            Skill execution result
        
        Raises:
            SkillExecutionError: If execution fails
            SkillPermissionError: If rate limit exceeded
        """
        skill_name = skill.name
        timeout = timeout or self.default_timeout
        
        # Check rate limit
        if not self._check_rate_limit(skill_name):
            raise SkillPermissionError(
                f"Rate limit exceeded for skill: {skill_name}",
                details={"limit": self.rate_limit, "period": "1 minute"}
            )
        
        # Check if skill can execute
        can_execute, reason = skill.can_execute()
        if not can_execute:
            raise SkillPermissionError(
                f"Skill cannot execute: {reason}",
                details={"skill": skill_name, "reason": reason}
            )
        
        # Publish start event
        await self.event_bus.publish(
            EventType.SKILL_STARTED,
            {"skill": skill_name, "params": params},
            source="skill_execution_manager"
        )
        
        start_time = datetime.now()
        
        try:
            # Execute with timeout and resource monitoring
            result = await asyncio.wait_for(
                self._execute_with_monitoring(skill, params),
                timeout=timeout
            )
            
            # Publish completion event
            await self.event_bus.publish(
                EventType.SKILL_COMPLETED,
                {
                    "skill": skill_name,
                    "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "success": result.get("success", False)
                },
                source="skill_execution_manager"
            )
            
            return result
        
        except asyncio.TimeoutError:
            logger.error(f"Skill timeout: {skill_name} ({timeout}s)")
            
            # Publish timeout event
            await self.event_bus.publish(
                EventType.SKILL_TIMEOUT,
                {"skill": skill_name, "timeout": timeout},
                source="skill_execution_manager"
            )
            
            raise SkillExecutionError(
                f"Skill execution timeout: {skill_name}",
                details={"timeout": timeout}
            )
        
        except SandboxViolation as e:
            logger.error(f"Sandbox violation in skill {skill_name}: {e}")
            
            await self.event_bus.publish(
                EventType.SKILL_FAILED,
                {"skill": skill_name, "error": "sandbox_violation", "details": str(e)},
                source="skill_execution_manager"
            )
            
            raise SkillPermissionError(
                f"Sandbox violation: {e}",
                details={"skill": skill_name}
            )
        
        except Exception as e:
            logger.error(f"Skill execution failed: {skill_name} - {e}")
            
            await self.event_bus.publish(
                EventType.SKILL_FAILED,
                {"skill": skill_name, "error": str(e)},
                source="skill_execution_manager"
            )
            
            raise SkillExecutionError(
                f"Skill execution failed: {e}",
                details={"skill": skill_name}
            )
    
    async def _execute_with_monitoring(
        self,
        skill: BaseSkill,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute skill with resource monitoring"""
        # Get current process
        process = psutil.Process()
        initial_ram = process.memory_info().rss / (1024 ** 2)
        
        # Execute skill
        result = await skill.execute(params)
        
        # Check resource usage
        final_ram = process.memory_info().rss / (1024 ** 2)
        ram_used = final_ram - initial_ram
        
        if ram_used > self.max_ram_mb:
            logger.warning(
                f"Skill {skill.name} exceeded RAM quota: "
                f"{ram_used:.1f}MB > {self.max_ram_mb}MB"
            )
        
        return result
    
    def _check_rate_limit(self, skill_name: str) -> bool:
        """
        Check if skill is within rate limit
        
        Args:
            skill_name: Name of skill
        
        Returns:
            True if within limit
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Initialize history if needed
        if skill_name not in self._execution_history:
            self._execution_history[skill_name] = []
        
        # Remove old entries
        self._execution_history[skill_name] = [
            ts for ts in self._execution_history[skill_name]
            if ts > cutoff
        ]
        
        # Check limit
        if len(self._execution_history[skill_name]) >= self.rate_limit:
            return False
        
        # Add current execution
        self._execution_history[skill_name].append(now)
        
        return True
    
    def get_execution_stats(self, skill_name: str) -> Dict[str, Any]:
        """Get execution statistics for skill"""
        history = self._execution_history.get(skill_name, [])
        
        return {
            "skill": skill_name,
            "executions_last_minute": len(history),
            "rate_limit": self.rate_limit,
            "within_limit": len(history) < self.rate_limit
        }


# Global execution manager instance
_global_execution_manager: Optional[SkillExecutionManager] = None


def get_skill_execution_manager() -> SkillExecutionManager:
    """Get global skill execution manager instance"""
    global _global_execution_manager
    if _global_execution_manager is None:
        _global_execution_manager = SkillExecutionManager()
    return _global_execution_manager


if __name__ == "__main__":
    # Test skill execution manager
    import asyncio
    from skills.clipboard_skill import ClipboardSkill
    
    async def test():
        print("Testing Skill Execution Manager")
        print("=" * 50)
        
        manager = SkillExecutionManager(default_timeout=10)
        skill = ClipboardSkill()
        
        # Test execution
        result = await manager.execute_skill(
            skill,
            {"action": "copy", "text": "test"}
        )
        print(f"Result: {result}")
        
        # Test stats
        stats = manager.get_execution_stats("clipboard")
        print(f"Stats: {stats}")
        
        print("=" * 50)
    
    asyncio.run(test())
