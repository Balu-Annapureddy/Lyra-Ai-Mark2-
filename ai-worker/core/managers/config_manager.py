"""
Configuration Manager with Versioning and Auto-Migration
Handles loading, validating, and migrating configuration files
"""

import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration files with versioning and automatic migration"""
    
    CURRENT_VERSION = "1.0"
    
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.migrations: Dict[str, callable] = {
            "1.0->1.1": self._migrate_1_0_to_1_1,
        }
    
    def load_yaml(self, filename: str, required: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load and validate a YAML configuration file
        
        Args:
            filename: Name of the config file (e.g., 'performance_modes.yaml')
            required: If True, raise error if file doesn't exist
            
        Returns:
            Configuration dictionary or None if file doesn't exist and not required
        """
        filepath = self.config_dir / filename
        
        # Check cache first
        if filename in self.config_cache:
            return self.config_cache[filename]
        
        # Check if file exists
        if not filepath.exists():
            if required:
                logger.warning(f"Config file {filename} not found, creating default")
                self._create_default_config(filename)
            else:
                return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                config = {}
            
            # Check version and migrate if needed
            config = self._check_and_migrate(filename, config)
            
            # Cache the config
            self.config_cache[filename] = config
            
            logger.info(f"Loaded config: {filename} (version {config.get('config_version', 'unknown')})")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config {filename}: {e}")
            if required:
                raise
            return None
    
    def load_json(self, filename: str, required: bool = True) -> Optional[Dict[str, Any]]:
        """Load and validate a JSON configuration file"""
        filepath = self.config_dir / filename
        
        if filename in self.config_cache:
            return self.config_cache[filename]
        
        if not filepath.exists():
            if required:
                logger.warning(f"Config file {filename} not found, creating default")
                self._create_default_config(filename)
            else:
                return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Check version and migrate if needed
            config = self._check_and_migrate(filename, config)
            
            self.config_cache[filename] = config
            logger.info(f"Loaded config: {filename}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config {filename}: {e}")
            if required:
                raise
            return None
    
    def save_yaml(self, filename: str, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file"""
        filepath = self.config_dir / filename
        
        # Ensure config has version
        if 'config_version' not in config:
            config['config_version'] = self.CURRENT_VERSION
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            # Update cache
            self.config_cache[filename] = config
            logger.info(f"Saved config: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save config {filename}: {e}")
            raise
    
    def save_json(self, filename: str, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file"""
        filepath = self.config_dir / filename
        
        # Ensure config has version
        if 'config_version' not in config:
            config['config_version'] = self.CURRENT_VERSION
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            self.config_cache[filename] = config
            logger.info(f"Saved config: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save config {filename}: {e}")
            raise
    
    def _check_and_migrate(self, filename: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check config version and migrate if necessary"""
        current_version = config.get('config_version', '1.0')
        
        if current_version == self.CURRENT_VERSION:
            return config
        
        # Backup before migration
        self._backup_config(filename)
        
        # Perform migration
        migration_key = f"{current_version}->{self.CURRENT_VERSION}"
        if migration_key in self.migrations:
            logger.info(f"Migrating {filename} from {current_version} to {self.CURRENT_VERSION}")
            config = self.migrations[migration_key](config)
            config['config_version'] = self.CURRENT_VERSION
            
            # Save migrated config
            if filename.endswith('.yaml'):
                self.save_yaml(filename, config)
            else:
                self.save_json(filename, config)
        else:
            logger.warning(f"No migration path from {current_version} to {self.CURRENT_VERSION}")
        
        return config
    
    def _backup_config(self, filename: str) -> None:
        """Create a backup of the config file before migration"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_dir / f"{filename}.backup_{timestamp}"
        
        try:
            shutil.copy2(filepath, backup_path)
            logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup for {filename}: {e}")
    
    def _create_default_config(self, filename: str) -> None:
        """Create default configuration file if it doesn't exist"""
        defaults = {
            'memory_watchdog.yaml': {
                'config_version': '1.0',
                'enabled': False,
                'soft_limit_percent': 95,
                'hard_limit_percent': 98,
                'check_interval': 30,
                'auto_adjust': True,
            },
            'permissions.json': {
                'config_version': '1.0',
                'microphone': False,
                'camera': False,
                'clipboard_read': False,
                'clipboard_write': False,
                'web_browse': False,
                'file_read': False,
                'file_write': False,
            },
            'model_registry.yaml': {
                'config_version': '1.0',
                'models': [],
            },
        }
        
        if filename in defaults:
            if filename.endswith('.yaml'):
                self.save_yaml(filename, defaults[filename])
            else:
                self.save_json(filename, defaults[filename])
    
    def _migrate_1_0_to_1_1(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migration from version 1.0 to 1.1"""
        # Example migration: add new fields, rename old ones
        # This is a placeholder for future migrations
        return config
    
    def reload(self, filename: str) -> Optional[Dict[str, Any]]:
        """Reload configuration from disk, bypassing cache"""
        if filename in self.config_cache:
            del self.config_cache[filename]
        
        if filename.endswith('.yaml'):
            return self.load_yaml(filename)
        else:
            return self.load_json(filename)
    
    def clear_cache(self) -> None:
        """Clear all cached configurations"""
        self.config_cache.clear()
        logger.info("Configuration cache cleared")


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: Optional[Path] = None) -> ConfigManager:
    """
    Get or create the global config manager
    
    Args:
        config_dir: Directory containing config files (required for first call)
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    
    if _config_manager is None:
        if config_dir is None:
            # Default to 'config' directory in current working directory
            config_dir = Path("config")
            if not config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
        
        _config_manager = ConfigManager(config_dir)
    
    return _config_manager
