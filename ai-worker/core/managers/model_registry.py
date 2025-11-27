"""
Model Registry - Model Catalog Management
Manages model catalog with RAM-based filtering and compatibility checking
"""

import logging
import psutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from core.managers.config_manager import ConfigManager
from error.error_handler import ErrorHandler, LyraError
from error.error_codes import ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a model"""
    id: str
    name: str
    type: str  # llm, stt, tts, vision
    size_gb: float
    ram_required_gb: float
    download_url: str
    local_path: str
    enabled: bool
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        """Create from dictionary"""
        return cls(**data)


class ModelRegistry:
    """
    Manages model catalog with RAM-based filtering
    
    Features:
    - Load models from config/model_registry.yaml
    - Filter models by RAM compatibility
    - Filter models by type (llm, stt, tts, vision)
    - Check if specific model is compatible
    """
    
    def __init__(self, config_manager: ConfigManager, error_handler: ErrorHandler):
        """
        Initialize model registry
        
        Args:
            config_manager: ConfigManager instance for loading model registry
            error_handler: ErrorHandler instance for error responses
        """
        self.config_manager = config_manager
        self.error_handler = error_handler
        self.models: List[ModelInfo] = []
        self._available_ram_gb: float = 0.0
        self._load_registry()
        self._detect_available_ram()
    
    def _load_registry(self) -> None:
        """Load model registry from config file"""
        try:
            config = self.config_manager.load_yaml("model_registry.yaml", required=True)
            
            if not config or "models" not in config:
                logger.warning("No models found in registry")
                self.models = []
                return
            
            # Parse models
            self.models = []
            for model_data in config["models"]:
                try:
                    model = ModelInfo.from_dict(model_data)
                    self.models.append(model)
                except Exception as e:
                    logger.error(f"Failed to parse model {model_data.get('id', 'unknown')}: {e}")
            
            logger.info(f"Loaded {len(self.models)} models from registry")
        
        except Exception as e:
            logger.error(f"Failed to load model registry: {e}")
            raise LyraError(ErrorCode.MODEL_REGISTRY_LOAD_FAIL, str(e))
    
    def _detect_available_ram(self) -> None:
        """Detect available system RAM"""
        try:
            mem = psutil.virtual_memory()
            self._available_ram_gb = mem.total / (1024 ** 3)
            logger.info(f"Detected {self._available_ram_gb:.2f} GB total RAM")
        except Exception as e:
            logger.error(f"Failed to detect RAM: {e}")
            self._available_ram_gb = 8.0  # Default fallback
    
    def get_available_models(self, model_type: Optional[str] = None) -> List[ModelInfo]:
        """
        Get models that fit in available RAM
        
        Args:
            model_type: Optional filter by model type (llm, stt, tts, vision)
            
        Returns:
            List of compatible ModelInfo objects
        """
        compatible_models = []
        
        for model in self.models:
            # Skip disabled models
            if not model.enabled:
                continue
            
            # Filter by type if specified
            if model_type and model.type != model_type:
                continue
            
            # Check RAM compatibility
            if model.ram_required_gb <= self._available_ram_gb:
                compatible_models.append(model)
        
        logger.debug(
            f"Found {len(compatible_models)} compatible models" +
            (f" of type {model_type}" if model_type else "")
        )
        
        return compatible_models
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model
        
        Args:
            model_id: Model ID to look up
            
        Returns:
            ModelInfo object or None if not found
        """
        for model in self.models:
            if model.id == model_id:
                return model
        
        logger.warning(f"Model not found: {model_id}")
        return None
    
    def is_model_compatible(self, model_id: str) -> bool:
        """
        Check if a model is compatible with current system RAM
        
        Args:
            model_id: Model ID to check
            
        Returns:
            True if compatible, False otherwise
        """
        model = self.get_model_info(model_id)
        
        if model is None:
            return False
        
        if not model.enabled:
            logger.debug(f"Model {model_id} is disabled")
            return False
        
        compatible = model.ram_required_gb <= self._available_ram_gb
        
        if not compatible:
            logger.debug(
                f"Model {model_id} requires {model.ram_required_gb:.2f} GB RAM, "
                f"but only {self._available_ram_gb:.2f} GB available"
            )
        
        return compatible
    
    def get_compatible_models(self, model_type: str) -> List[ModelInfo]:
        """
        Get all compatible models of a specific type
        
        Args:
            model_type: Model type (llm, stt, tts, vision)
            
        Returns:
            List of compatible ModelInfo objects
        """
        return self.get_available_models(model_type=model_type)
    
    def get_all_models(self, include_disabled: bool = False) -> List[ModelInfo]:
        """
        Get all models in registry
        
        Args:
            include_disabled: Whether to include disabled models
            
        Returns:
            List of all ModelInfo objects
        """
        if include_disabled:
            return self.models.copy()
        else:
            return [m for m in self.models if m.enabled]
    
    def get_models_by_type(self, model_type: str, include_disabled: bool = False) -> List[ModelInfo]:
        """
        Get all models of a specific type
        
        Args:
            model_type: Model type (llm, stt, tts, vision)
            include_disabled: Whether to include disabled models
            
        Returns:
            List of ModelInfo objects
        """
        models = self.get_all_models(include_disabled=include_disabled)
        return [m for m in models if m.type == model_type]
    
    def reload_registry(self) -> None:
        """Reload model registry from config file"""
        logger.info("Reloading model registry")
        self._load_registry()
        self._detect_available_ram()
    
    def get_available_ram_gb(self) -> float:
        """
        Get available system RAM in GB
        
        Returns:
            Available RAM in GB
        """
        return self._available_ram_gb
    
    def check_model_compatibility_or_raise(self, model_id: str) -> ModelInfo:
        """
        Check model compatibility and raise error if incompatible
        
        Args:
            model_id: Model ID to check
            
        Returns:
            ModelInfo object
            
        Raises:
            LyraError: If model not found or incompatible
        """
        model = self.get_model_info(model_id)
        
        if model is None:
            raise LyraError(
                ErrorCode.MODEL_NOT_FOUND,
                f"Model '{model_id}' not found in registry"
            )
        
        if not model.enabled:
            raise LyraError(
                ErrorCode.MODEL_NOT_COMPATIBLE,
                f"Model '{model_id}' is disabled"
            )
        
        if not self.is_model_compatible(model_id):
            raise LyraError(
                ErrorCode.MODEL_NOT_COMPATIBLE,
                f"Model '{model_id}' requires {model.ram_required_gb:.2f} GB RAM, "
                f"but only {self._available_ram_gb:.2f} GB available"
            )
        
        return model
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check for model registry
        
        Returns:
            Dictionary with health status
        """
        return {
            "status": "ok",
            "models_total": len(self.models),
            "models_enabled": len([m for m in self.models if m.enabled]),
            "models_compatible": len(self.get_available_models()),
            "available_ram_gb": round(self._available_ram_gb, 2),
        }


# Singleton instance management
_model_registry: Optional[ModelRegistry] = None


def get_model_registry(
    config_manager: Optional[ConfigManager] = None,
    error_handler: Optional[ErrorHandler] = None
) -> ModelRegistry:
    """
    Get or create the global model registry
    
    Args:
        config_manager: ConfigManager instance (required for first call)
        error_handler: ErrorHandler instance (required for first call)
        
    Returns:
        ModelRegistry instance
    """
    global _model_registry
    
    if _model_registry is None:
        if config_manager is None or error_handler is None:
            raise ValueError("config_manager and error_handler required for first call")
        _model_registry = ModelRegistry(config_manager, error_handler)
    
    return _model_registry
