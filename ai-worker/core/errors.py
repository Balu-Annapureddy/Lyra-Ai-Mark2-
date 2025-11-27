"""
Unified Error Classes for All Modules
Provides consistent error handling across the entire application
"""

from typing import Optional, Dict, Any


class LyraError(Exception):
    """Base exception for all Lyra errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Lyra error
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Safety & Resource Errors
class SafetyError(LyraError):
    """Base class for safety-related errors"""
    pass


class TimeoutError(SafetyError):
    """Operation exceeded timeout"""
    pass


class MemoryLimitError(SafetyError):
    """Memory limit exceeded"""
    pass


class ResourceExhaustedError(SafetyError):
    """System resources exhausted"""
    pass


# Model Errors
class ModelError(LyraError):
    """Base class for model-related errors"""
    pass


class ModelNotFoundError(ModelError):
    """Model not found or not installed"""
    pass


class ModelLoadError(ModelError):
    """Failed to load model"""
    pass


class ModelDownloadError(ModelError):
    """Failed to download model"""
    pass


class ModelVerificationError(ModelError):
    """Model verification failed (SHA256 mismatch)"""
    pass


# Configuration Errors
class ConfigError(LyraError):
    """Base class for configuration errors"""
    pass


class ConfigValidationError(ConfigError):
    """Configuration validation failed"""
    pass


class ConfigNotFoundError(ConfigError):
    """Configuration file not found"""
    pass


# Skill Errors
class SkillError(LyraError):
    """Base class for skill-related errors"""
    pass


class SkillNotFoundError(SkillError):
    """Skill not found"""
    pass


class SkillExecutionError(SkillError):
    """Skill execution failed"""
    pass


class SkillPermissionError(SkillError):
    """Insufficient permissions to execute skill"""
    pass


# Sandbox Errors
class SandboxError(LyraError):
    """Base class for sandbox-related errors"""
    pass


class SandboxViolation(SandboxError):
    """Sandbox security rules violated"""
    pass


class CommandNotAllowedError(SandboxViolation):
    """Command not in whitelist"""
    pass


class PathNotAllowedError(SandboxViolation):
    """Path not in allowed directories"""
    pass


# GPU Errors
class GPUError(LyraError):
    """Base class for GPU-related errors"""
    pass


class GPUNotAvailableError(GPUError):
    """GPU not available or not detected"""
    pass


class GPUMemoryError(GPUError):
    """Insufficient GPU memory"""
    pass


# State Errors
class StateError(LyraError):
    """Base class for state-related errors"""
    pass


class StateCorruptedError(StateError):
    """State data corrupted"""
    pass


class StateLockError(StateError):
    """Failed to acquire state lock"""
    pass


# Job Scheduler Errors
class JobError(LyraError):
    """Base class for job-related errors"""
    pass


class JobNotFoundError(JobError):
    """Job not found"""
    pass


class JobCancelledError(JobError):
    """Job was cancelled"""
    pass


class JobTimeoutError(JobError):
    """Job exceeded timeout"""
    pass


# API Errors
class APIError(LyraError):
    """Base class for API-related errors"""
    pass


class InvalidRequestError(APIError):
    """Invalid API request"""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded"""
    pass


# Helper functions
def format_error(error: Exception) -> Dict[str, Any]:
    """
    Format any exception as dictionary
    
    Args:
        error: Exception to format
    
    Returns:
        Error dictionary
    """
    if isinstance(error, LyraError):
        return error.to_dict()
    
    return {
        "error": error.__class__.__name__,
        "message": str(error),
        "details": {}
    }


def is_retryable_error(error: Exception) -> bool:
    """
    Check if error is retryable
    
    Args:
        error: Exception to check
    
    Returns:
        True if error is retryable
    """
    retryable_types = (
        TimeoutError,
        ResourceExhaustedError,
        ModelDownloadError,
        GPUMemoryError,
        JobTimeoutError
    )
    
    return isinstance(error, retryable_types)
