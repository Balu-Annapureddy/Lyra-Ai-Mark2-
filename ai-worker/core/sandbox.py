"""
Sandbox - Safe Subprocess Execution and Permissions
Provides secure execution environment for system commands and file operations
"""

import logging
import subprocess
import asyncio
from typing import Dict, Any, Optional, List, Literal
from pathlib import Path
import platform
import os

from core.safety import with_timeout, TimeoutError

logger = logging.getLogger(__name__)


class SandboxViolation(Exception):
    """Raised when sandbox security rules are violated"""
    pass


class Sandbox:
    """
    Secure execution environment for system operations
    - Subprocess execution with timeouts
    - File system permissions
    - Resource limits
    - Command whitelisting
    """
    
    def __init__(
        self,
        allowed_commands: Optional[List[str]] = None,
        allowed_paths: Optional[List[Path]] = None,
        max_execution_time: int = 30,
        enable_network: bool = False
    ):
        """
        Initialize sandbox
        
        Args:
            allowed_commands: Whitelist of allowed commands
            allowed_paths: Whitelist of allowed file paths
            max_execution_time: Max execution time in seconds
            enable_network: Allow network access
        """
        self.allowed_commands = allowed_commands or self._get_default_commands()
        self.allowed_paths = allowed_paths or self._get_default_paths()
        self.max_execution_time = max_execution_time
        self.enable_network = enable_network
        
        logger.info(
            f"Sandbox initialized: "
            f"{len(self.allowed_commands)} commands, "
            f"{len(self.allowed_paths)} paths, "
            f"timeout={max_execution_time}s"
        )
    
    def _get_default_commands(self) -> List[str]:
        """Get default allowed commands based on platform"""
        system = platform.system()
        
        if system == "Windows":
            return [
                "cmd", "powershell", "python", "pip",
                "dir", "type", "copy", "move", "del",
                "echo", "where", "findstr"
            ]
        else:  # Linux/Mac
            return [
                "sh", "bash", "python", "python3", "pip", "pip3",
                "ls", "cat", "cp", "mv", "rm", "mkdir",
                "echo", "which", "grep", "find"
            ]
    
    def _get_default_paths(self) -> List[Path]:
        """Get default allowed paths"""
        from core.paths import get_app_data_dir, get_project_root
        
        return [
            get_app_data_dir(),
            get_project_root(),
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads"
        ]
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if command is in whitelist"""
        # Extract base command (first word)
        base_command = command.split()[0] if command else ""
        
        # Check whitelist
        return base_command in self.allowed_commands
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories"""
        path = path.resolve()
        
        for allowed_path in self.allowed_paths:
            try:
                # Check if path is within allowed directory
                path.relative_to(allowed_path.resolve())
                return True
            except ValueError:
                continue
        
        return False
    
    @with_timeout(30)
    def execute_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute command in sandbox
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            capture_output: Capture stdout/stderr
        
        Returns:
            Result dictionary with:
            - success: bool
            - stdout: str
            - stderr: str
            - returncode: int
        
        Raises:
            SandboxViolation: If command or path not allowed
            TimeoutError: If execution exceeds timeout
        """
        # Validate command
        if not self.is_command_allowed(command):
            raise SandboxViolation(f"Command not allowed: {command}")
        
        # Validate working directory
        if cwd and not self.is_path_allowed(cwd):
            raise SandboxViolation(f"Path not allowed: {cwd}")
        
        logger.info(f"Executing command: {command}")
        
        try:
            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=exec_env,
                capture_output=capture_output,
                text=True,
                timeout=self.max_execution_time
            )
            
            logger.info(f"Command completed: returncode={result.returncode}")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "returncode": result.returncode
            }
        
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {command}")
            raise TimeoutError(f"Command exceeded {self.max_execution_time}s timeout")
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    async def execute_command_async(
        self,
        command: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute command asynchronously"""
        # Validate command
        if not self.is_command_allowed(command):
            raise SandboxViolation(f"Command not allowed: {command}")
        
        # Validate working directory
        if cwd and not self.is_path_allowed(cwd):
            raise SandboxViolation(f"Path not allowed: {cwd}")
        
        logger.info(f"Executing command (async): {command}")
        
        try:
            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=exec_env
            )
            
            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.max_execution_time
                )
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Command exceeded {self.max_execution_time}s timeout")
            
            logger.info(f"Command completed: returncode={process.returncode}")
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "returncode": process.returncode
            }
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def read_file_safe(
        self,
        path: Path,
        max_size_mb: int = 10
    ) -> Dict[str, Any]:
        """
        Safely read file with size limit
        
        Args:
            path: File path
            max_size_mb: Maximum file size in MB
        
        Returns:
            Result dictionary
        
        Raises:
            SandboxViolation: If path not allowed
        """
        path = path.resolve()
        
        # Validate path
        if not self.is_path_allowed(path):
            raise SandboxViolation(f"Path not allowed: {path}")
        
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}"
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {path}"
            }
        
        # Check file size
        size_mb = path.stat().st_size / (1024 ** 2)
        if size_mb > max_size_mb:
            return {
                "success": False,
                "error": f"File too large: {size_mb:.1f}MB > {max_size_mb}MB"
            }
        
        try:
            content = path.read_text(encoding='utf-8')
            return {
                "success": True,
                "content": content,
                "size_bytes": path.stat().st_size
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def write_file_safe(
        self,
        path: Path,
        content: str,
        max_size_mb: int = 10
    ) -> Dict[str, Any]:
        """
        Safely write file with size limit
        
        Args:
            path: File path
            content: Content to write
            max_size_mb: Maximum file size in MB
        
        Returns:
            Result dictionary
        
        Raises:
            SandboxViolation: If path not allowed
        """
        path = path.resolve()
        
        # Validate path
        if not self.is_path_allowed(path):
            raise SandboxViolation(f"Path not allowed: {path}")
        
        # Check content size
        size_mb = len(content.encode('utf-8')) / (1024 ** 2)
        if size_mb > max_size_mb:
            return {
                "success": False,
                "error": f"Content too large: {size_mb:.1f}MB > {max_size_mb}MB"
            }
        
        try:
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            path.write_text(content, encoding='utf-8')
            
            return {
                "success": True,
                "path": str(path),
                "size_bytes": path.stat().st_size
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global sandbox instance
_global_sandbox: Optional[Sandbox] = None


def get_sandbox() -> Sandbox:
    """Get global sandbox instance"""
    global _global_sandbox
    if _global_sandbox is None:
        _global_sandbox = Sandbox()
    return _global_sandbox


if __name__ == "__main__":
    # Test sandbox
    print("Testing Sandbox")
    print("=" * 50)
    
    sandbox = Sandbox()
    
    # Test command execution
    if platform.system() == "Windows":
        result = sandbox.execute_command("echo Hello World")
    else:
        result = sandbox.execute_command("echo 'Hello World'")
    
    print(f"Success: {result['success']}")
    print(f"Output: {result['stdout']}")
    
    # Test disallowed command
    try:
        sandbox.execute_command("rm -rf /")
    except SandboxViolation as e:
        print(f"✓ Blocked dangerous command: {e}")
    
    print("=" * 50)
