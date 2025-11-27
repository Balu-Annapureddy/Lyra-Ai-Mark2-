"""
Config Validator - YAML Configuration Validation
Validates configuration files against schemas
"""

import logging
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Configuration validation error"""
    field: str
    message: str
    severity: str  # "error" or "warning"


class ConfigValidator:
    """
    Validates YAML configuration files against schemas
    Ensures type safety and required fields
    """
    
    def __init__(self):
        """Initialize config validator"""
        self.schemas = self._define_schemas()
        logger.info("ConfigValidator initialized")
    
    def _define_schemas(self) -> Dict[str, Dict]:
        """Define configuration schemas"""
        return {
            "startup": {
                "safe_startup": {"type": bool, "required": True, "default": True},
                "lazy_import": {"type": bool, "required": True, "default": True},
                "warmup_enabled": {"type": bool, "required": True, "default": True},
                "auto_unload_timeout": {"type": int, "required": True, "default": 300, "min": 60, "max": 3600},
                "show_welcome_message": {"type": bool, "required": False, "default": True},
                "check_updates": {"type": bool, "required": False, "default": False},
                "debug_mode": {"type": bool, "required": False, "default": False},
                "verbose_logging": {"type": bool, "required": False, "default": False}
            },
            "performance_modes": {
                "low_power_mode": {
                    "type": dict,
                    "required": True,
                    "schema": {
                        "enabled": {"type": bool, "required": True},
                        "llm_model": {"type": str, "required": True},
                        "stt_model": {"type": str, "required": True},
                        "tts_engine": {"type": str, "required": True},
                        "vision_enabled": {"type": bool, "required": True},
                        "realtime_enabled": {"type": bool, "required": True},
                        "natural_tts_enabled": {"type": bool, "required": True},
                        "max_context_tokens": {"type": int, "required": True, "min": 512, "max": 8192},
                        "max_concurrent_requests": {"type": int, "required": True, "min": 1, "max": 10},
                        "background_workers": {"type": bool, "required": True},
                        "auto_unload_timeout": {"type": int, "required": True, "min": 60},
                        "force_gc_interval": {"type": int, "required": True, "min": 30}
                    }
                },
                "high_performance_mode": {
                    "type": dict,
                    "required": True,
                    "schema": {
                        "enabled": {"type": bool, "required": True},
                        "llm_model": {"type": str, "required": True},
                        "stt_model": {"type": str, "required": True},
                        "tts_engine": {"type": str, "required": True},
                        "vision_enabled": {"type": bool, "required": True},
                        "realtime_enabled": {"type": bool, "required": True},
                        "natural_tts_enabled": {"type": bool, "required": True},
                        "max_context_tokens": {"type": int, "required": True, "min": 512, "max": 16384},
                        "max_concurrent_requests": {"type": int, "required": True, "min": 1, "max": 20},
                        "background_workers": {"type": bool, "required": True},
                        "auto_unload_timeout": {"type": int, "required": True, "min": 60},
                        "force_gc_interval": {"type": int, "required": True, "min": 30}
                    }
                },
                "auto_detect": {
                    "type": dict,
                    "required": True,
                    "schema": {
                        "enabled": {"type": bool, "required": True},
                        "min_ram_for_high_perf": {"type": float, "required": True, "min": 8.0, "max": 64.0},
                        "safety_buffer_gb": {"type": float, "required": True, "min": 1.0, "max": 8.0}
                    }
                }
            }
        }
    
    def validate_config(
        self,
        config: Dict[str, Any],
        schema_name: str
    ) -> tuple[bool, List[ValidationError]]:
        """
        Validate configuration against schema
        
        Args:
            config: Configuration dictionary
            schema_name: Name of schema to validate against
        
        Returns:
            (is_valid, list_of_errors)
        """
        if schema_name not in self.schemas:
            return False, [ValidationError(
                field="schema",
                message=f"Unknown schema: {schema_name}",
                severity="error"
            )]
        
        schema = self.schemas[schema_name]
        errors = []
        
        # Validate each field
        for field_name, field_schema in schema.items():
            errors.extend(
                self._validate_field(config, field_name, field_schema, [])
            )
        
        # Check for unknown fields (warnings)
        for field_name in config.keys():
            if field_name not in schema:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"Unknown field: {field_name}",
                    severity="warning"
                ))
        
        is_valid = not any(e.severity == "error" for e in errors)
        return is_valid, errors
    
    def _validate_field(
        self,
        config: Dict[str, Any],
        field_name: str,
        field_schema: Dict[str, Any],
        path: List[str]
    ) -> List[ValidationError]:
        """Validate a single field"""
        errors = []
        full_path = ".".join(path + [field_name])
        
        # Check if field exists
        if field_name not in config:
            if field_schema.get("required", False):
                errors.append(ValidationError(
                    field=full_path,
                    message=f"Required field missing: {field_name}",
                    severity="error"
                ))
            return errors
        
        value = config[field_name]
        expected_type = field_schema.get("type")
        
        # Type validation
        if expected_type and not isinstance(value, expected_type):
            errors.append(ValidationError(
                field=full_path,
                message=f"Invalid type: expected {expected_type.__name__}, got {type(value).__name__}",
                severity="error"
            ))
            return errors
        
        # Nested schema validation
        if expected_type == dict and "schema" in field_schema:
            nested_schema = field_schema["schema"]
            for nested_field, nested_field_schema in nested_schema.items():
                errors.extend(
                    self._validate_field(
                        value,
                        nested_field,
                        nested_field_schema,
                        path + [field_name]
                    )
                )
        
        # Range validation for numbers
        if isinstance(value, (int, float)):
            if "min" in field_schema and value < field_schema["min"]:
                errors.append(ValidationError(
                    field=full_path,
                    message=f"Value {value} below minimum {field_schema['min']}",
                    severity="error"
                ))
            
            if "max" in field_schema and value > field_schema["max"]:
                errors.append(ValidationError(
                    field=full_path,
                    message=f"Value {value} above maximum {field_schema['max']}",
                    severity="error"
                ))
        
        return errors
    
    def load_and_validate(
        self,
        config_path: Path,
        schema_name: str
    ) -> tuple[Optional[Dict], List[ValidationError]]:
        """
        Load YAML config and validate
        
        Args:
            config_path: Path to YAML config file
            schema_name: Schema to validate against
        
        Returns:
            (config_dict or None, list_of_errors)
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            is_valid, errors = self.validate_config(config, schema_name)
            
            if is_valid:
                logger.info(f"Config validated successfully: {config_path}")
                return config, errors
            else:
                logger.error(f"Config validation failed: {config_path}")
                for error in errors:
                    if error.severity == "error":
                        logger.error(f"  {error.field}: {error.message}")
                    else:
                        logger.warning(f"  {error.field}: {error.message}")
                return None, errors
        
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None, [ValidationError(
                field="file",
                message=str(e),
                severity="error"
            )]
    
    def apply_defaults(
        self,
        config: Dict[str, Any],
        schema_name: str
    ) -> Dict[str, Any]:
        """
        Apply default values from schema
        
        Args:
            config: Configuration dictionary
            schema_name: Schema name
        
        Returns:
            Config with defaults applied
        """
        if schema_name not in self.schemas:
            return config
        
        schema = self.schemas[schema_name]
        result = config.copy()
        
        for field_name, field_schema in schema.items():
            if field_name not in result and "default" in field_schema:
                result[field_name] = field_schema["default"]
                logger.debug(f"Applied default for {field_name}: {field_schema['default']}")
        
        return result


# Global validator instance
_global_validator: Optional[ConfigValidator] = None


def get_config_validator() -> ConfigValidator:
    """Get global config validator instance"""
    global _global_validator
    if _global_validator is None:
        _global_validator = ConfigValidator()
    return _global_validator


if __name__ == "__main__":
    # Test config validator
    print("Testing Config Validator")
    print("=" * 50)
    
    validator = ConfigValidator()
    
    # Test valid config
    test_config = {
        "safe_startup": True,
        "lazy_import": True,
        "warmup_enabled": True,
        "auto_unload_timeout": 300
    }
    
    is_valid, errors = validator.validate_config(test_config, "startup")
    print(f"Valid: {is_valid}")
    print(f"Errors: {len(errors)}")
    
    for error in errors:
        print(f"  [{error.severity}] {error.field}: {error.message}")
    
    print("=" * 50)
