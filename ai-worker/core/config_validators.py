"""
Configuration Validators
Validates configuration files and provides default fallbacks
"""

import logging
from typing import Any, Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration values and provides defaults"""
    
    @staticmethod
    def validate_percentage(
        value: Any,
        field_name: str,
        default: float,
        min_val: float = 0.0,
        max_val: float = 100.0
    ) -> float:
        """
        Validate percentage value
        
        Args:
            value: Value to validate
            field_name: Name of the field (for logging)
            default: Default value if invalid
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Validated percentage value
        """
        try:
            val = float(value)
            if val < min_val or val > max_val:
                logger.warning(
                    f"Config validation: {field_name}={val} out of range "
                    f"[{min_val}, {max_val}]. Using default: {default}"
                )
                return default
            return val
        except (TypeError, ValueError):
            logger.warning(
                f"Config validation: {field_name}={value} is not a valid number. "
                f"Using default: {default}"
            )
            return default
    
    @staticmethod
    def validate_positive_number(
        value: Any,
        field_name: str,
        default: float,
        min_val: float = 0.0
    ) -> float:
        """
        Validate positive number
        
        Args:
            value: Value to validate
            field_name: Name of the field
            default: Default value if invalid
            min_val: Minimum allowed value
            
        Returns:
            Validated number
        """
        try:
            val = float(value)
            if val < min_val:
                logger.warning(
                    f"Config validation: {field_name}={val} below minimum {min_val}. "
                    f"Using default: {default}"
                )
                return default
            return val
        except (TypeError, ValueError):
            logger.warning(
                f"Config validation: {field_name}={value} is not a valid number. "
                f"Using default: {default}"
            )
            return default
    
    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        default: int,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> int:
        """
        Validate integer value
        
        Args:
            value: Value to validate
            field_name: Name of the field
            default: Default value if invalid
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Validated integer
        """
        try:
            val = int(value)
            
            if min_val is not None and val < min_val:
                logger.warning(
                    f"Config validation: {field_name}={val} below minimum {min_val}. "
                    f"Using default: {default}"
                )
                return default
            
            if max_val is not None and val > max_val:
                logger.warning(
                    f"Config validation: {field_name}={val} above maximum {max_val}. "
                    f"Using default: {default}"
                )
                return default
            
            return val
        except (TypeError, ValueError):
            logger.warning(
                f"Config validation: {field_name}={value} is not a valid integer. "
                f"Using default: {default}"
            )
            return default
    
    @staticmethod
    def validate_boolean(
        value: Any,
        field_name: str,
        default: bool
    ) -> bool:
        """
        Validate boolean value
        
        Args:
            value: Value to validate
            field_name: Name of the field
            default: Default value if invalid
            
        Returns:
            Validated boolean
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', 'yes', '1', 'on'):
                return True
            if value.lower() in ('false', 'no', '0', 'off'):
                return False
        
        logger.warning(
            f"Config validation: {field_name}={value} is not a valid boolean. "
            f"Using default: {default}"
        )
        return default
    
    @staticmethod
    def validate_string_list(
        value: Any,
        field_name: str,
        default: List[str]
    ) -> List[str]:
        """
        Validate list of strings
        
        Args:
            value: Value to validate
            field_name: Name of the field
            default: Default value if invalid
            
        Returns:
            Validated list of strings
        """
        if isinstance(value, list):
            # Ensure all items are strings
            try:
                return [str(item) for item in value]
            except Exception:
                logger.warning(
                    f"Config validation: {field_name} contains non-string items. "
                    f"Using default: {default}"
                )
                return default
        
        logger.warning(
            f"Config validation: {field_name}={value} is not a list. "
            f"Using default: {default}"
        )
        return default


class MemoryWatchdogValidator:
    """Validator for memory watchdog configuration"""
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate memory watchdog configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validated configuration with defaults
        """
        validated = {}
        
        # Validate enabled flag
        validated['enabled'] = ConfigValidator.validate_boolean(
            config.get('enabled', False),
            'enabled',
            default=False
        )
        
        # Validate soft limit (must be less than hard limit)
        soft_limit = ConfigValidator.validate_percentage(
            config.get('soft_limit_percent', 75.0),
            'soft_limit_percent',
            default=75.0,
            min_val=50.0,
            max_val=95.0
        )
        
        # Validate hard limit
        hard_limit = ConfigValidator.validate_percentage(
            config.get('hard_limit_percent', 90.0),
            'hard_limit_percent',
            default=90.0,
            min_val=60.0,
            max_val=99.0
        )
        
        # Ensure soft < hard
        if soft_limit >= hard_limit:
            logger.warning(
                f"Config validation: soft_limit ({soft_limit}) >= hard_limit ({hard_limit}). "
                f"Adjusting soft_limit to {hard_limit - 10}"
            )
            soft_limit = hard_limit - 10
        
        validated['soft_limit_percent'] = soft_limit
        validated['hard_limit_percent'] = hard_limit
        
        # Validate check interval
        validated['check_interval'] = ConfigValidator.validate_integer(
            config.get('check_interval', 10),
            'check_interval',
            default=10,
            min_val=1,
            max_val=300
        )
        
        # Validate auto-adjust settings
        validated['auto_adjust'] = ConfigValidator.validate_boolean(
            config.get('auto_adjust', True),
            'auto_adjust',
            default=True
        )
        
        validated['low_ram_threshold_gb'] = ConfigValidator.validate_positive_number(
            config.get('low_ram_threshold_gb', 8.0),
            'low_ram_threshold_gb',
            default=8.0,
            min_val=2.0
        )
        
        validated['low_ram_soft_limit'] = ConfigValidator.validate_percentage(
            config.get('low_ram_soft_limit', 85.0),
            'low_ram_soft_limit',
            default=85.0
        )
        
        validated['low_ram_hard_limit'] = ConfigValidator.validate_percentage(
            config.get('low_ram_hard_limit', 95.0),
            'low_ram_hard_limit',
            default=95.0
        )
        
        return validated


class ModelRegistryValidator:
    """Validator for model registry configuration"""
    
    @staticmethod
    def validate_model(model: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate a single model entry
        
        Args:
            model: Model dictionary
            
        Returns:
            Validated model or None if invalid
        """
        # Required fields
        if 'id' not in model or 'name' not in model:
            logger.error(f"Config validation: Model missing required 'id' or 'name' field")
            return None
        
        validated = {
            'id': str(model['id']),
            'name': str(model['name']),
        }
        
        # Validate type
        valid_types = ['llm', 'stt', 'tts', 'vision']
        model_type = model.get('type', 'llm')
        if model_type not in valid_types:
            logger.warning(
                f"Config validation: Model {validated['id']} has invalid type '{model_type}'. "
                f"Using 'llm'"
            )
            model_type = 'llm'
        validated['type'] = model_type
        
        # Validate sizes
        validated['size_gb'] = ConfigValidator.validate_positive_number(
            model.get('size_gb', 1.0),
            f"model.{validated['id']}.size_gb",
            default=1.0,
            min_val=0.1
        )
        
        validated['ram_required_gb'] = ConfigValidator.validate_positive_number(
            model.get('ram_required_gb', 2.0),
            f"model.{validated['id']}.ram_required_gb",
            default=2.0,
            min_val=0.5
        )
        
        # Optional fields
        validated['download_url'] = str(model.get('download_url', ''))
        validated['local_path'] = str(model.get('local_path', ''))
        validated['enabled'] = ConfigValidator.validate_boolean(
            model.get('enabled', True),
            f"model.{validated['id']}.enabled",
            default=True
        )
        validated['description'] = str(model.get('description', ''))
        
        # Extended fields (Phase 1 enhancements)
        validated['quantization'] = str(model.get('quantization', ''))
        validated['architecture'] = str(model.get('architecture', ''))
        validated['provider'] = str(model.get('provider', 'local'))
        validated['tags'] = ConfigValidator.validate_string_list(
            model.get('tags', []),
            f"model.{validated['id']}.tags",
            default=[]
        )
        
        return validated
