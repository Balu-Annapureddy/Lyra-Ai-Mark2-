"""
Fail-Safe Recovery Boot System
Ensures Lyra always boots even with corrupted configurations
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FailSafe:
    """Handles fail-safe boot and configuration recovery"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.recovery_mode = False
        self.failed_configs = []
    
    def safe_boot(self) -> bool:
        """
        Attempt to boot with existing configs, fall back to safe mode if needed
        
        Returns:
            True if boot successful, False if in recovery mode
        """
        try:
            # Try to load critical configs
            critical_configs = [
                'performance_modes.yaml',
                'permissions.json',
            ]
            
            for config_file in critical_configs:
                if not self._validate_config(config_file):
                    logger.warning(f"Config validation failed: {config_file}")
                    self.failed_configs.append(config_file)
            
            if self.failed_configs:
                logger.warning(f"Entering safe mode due to {len(self.failed_configs)} failed configs")
                self._enter_safe_mode()
                return False
            
            logger.info("Boot successful with existing configurations")
            return True
            
        except Exception as e:
            logger.error(f"Critical boot error: {e}")
            self._enter_safe_mode()
            return False
    
    def _validate_config(self, filename: str) -> bool:
        """Validate a configuration file"""
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Config file missing: {filename}")
            return False
        
        try:
            if filename.endswith('.yaml'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Basic validation
            if config is None:
                return False
            
            # Check for config_version (optional but recommended)
            if 'config_version' not in config:
                logger.warning(f"Config {filename} missing version field")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate {filename}: {e}")
            return False
    
    def _enter_safe_mode(self) -> None:
        """Enter safe mode with minimal configuration"""
        self.recovery_mode = True
        logger.warning("=" * 60)
        logger.warning("ENTERING SAFE MODE - RECOVERY REQUIRED")
        logger.warning("=" * 60)
        
        # Regenerate failed configs
        for config_file in self.failed_configs:
            self._regenerate_config(config_file)
        
        # Create safe mode config
        self._create_safe_mode_config()
    
    def _regenerate_config(self, filename: str) -> None:
        """Regenerate a missing or corrupted config file"""
        logger.info(f"Regenerating config: {filename}")
        
        defaults = self._get_default_config(filename)
        if not defaults:
            logger.error(f"No default config available for {filename}")
            return
        
        filepath = self.config_dir / filename
        
        try:
            if filename.endswith('.yaml'):
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(defaults, f, default_flow_style=False, sort_keys=False)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(defaults, f, indent=2)
            
            logger.info(f"Successfully regenerated: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to regenerate {filename}: {e}")
    
    def _get_default_config(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get default configuration for a file"""
        defaults = {
            'performance_modes.yaml': {
                'config_version': '1.0',
                'low_power_mode': {
                    'enabled': True,
                    'llm_model': 'phi-3-mini-1.8b',
                    'stt_model': 'whisper-tiny',
                    'tts_engine': 'pyttsx3',
                    'vision_enabled': False,
                    'realtime_enabled': True,
                    'natural_tts_enabled': False,
                    'max_context_tokens': 2048,
                    'max_concurrent_requests': 2,
                    'background_workers': False,
                    'auto_unload_timeout': 300,
                    'force_gc_interval': 60,
                },
                'high_performance_mode': {
                    'enabled': False,
                },
                'auto_detect': {
                    'enabled': True,
                    'min_ram_for_high_perf': 14.0,
                    'safety_buffer_gb': 2.0,
                }
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
            'memory_watchdog.yaml': {
                'config_version': '1.0',
                'enabled': False,
                'soft_limit_percent': 95,
                'hard_limit_percent': 98,
                'check_interval': 30,
                'auto_adjust': True,
            },
            'model_registry.yaml': {
                'config_version': '1.0',
                'models': [],
            },
        }
        
        return defaults.get(filename)
    
    def _create_safe_mode_config(self) -> None:
        """Create a minimal safe mode configuration"""
        safe_config = {
            'config_version': '1.0',
            'mode': 'safe',
            'features': ['text_chat_only'],
            'models': [],
            'permissions': 'all_denied',
            'recovery_mode': True,
            'failed_configs': self.failed_configs,
        }
        
        safe_config_path = self.config_dir / 'safe_mode.yaml'
        
        try:
            with open(safe_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(safe_config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Created safe mode config: {safe_config_path}")
            
        except Exception as e:
            logger.error(f"Failed to create safe mode config: {e}")
    
    def is_recovery_mode(self) -> bool:
        """Check if system is in recovery mode"""
        return self.recovery_mode
    
    def get_recovery_info(self) -> Dict[str, Any]:
        """Get information about recovery mode"""
        return {
            'recovery_mode': self.recovery_mode,
            'failed_configs': self.failed_configs,
            'message': 'System started in safe mode. Some configurations were regenerated.',
        }
