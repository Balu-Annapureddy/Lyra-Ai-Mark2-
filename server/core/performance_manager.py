"""
Performance Manager - Auto-Select Mode Based on Hardware
"""

import psutil
import yaml
import logging
from pathlib import Path
from typing import Dict, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMode:
    """Performance mode configuration"""
    name: str
    llm_model: str
    stt_model: str
    tts_engine: str
    vision_enabled: bool
    realtime_enabled: bool
    natural_tts_enabled: bool
    max_context_tokens: int
    max_concurrent_requests: int
    background_workers: bool
    auto_unload_timeout: int
    force_gc_interval: int
    expected_ram_gb: float


class PerformanceManager:
    """Manages performance modes and auto-detection"""
    
    def __init__(self, config_path: Path = None):
        """
        Initialize performance manager
        
        Args:
            config_path: Path to performance_modes.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "performance_modes.yaml"
        
        self.config_path = config_path
        self.config = self._load_config()
        self.current_mode: PerformanceMode = None
        
        # Auto-detect and set mode
        if self.config.get("auto_detect", {}).get("enabled", True):
            self.auto_select_mode()
        else:
            # Default to low power
            self.set_mode("low_power")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded performance config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load performance config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "low_power_mode": {
                "enabled": True,
                "llm_model": "phi-3-mini-1.8b",
                "stt_model": "whisper-tiny",
                "tts_engine": "pyttsx3",
                "vision_enabled": False,
                "realtime_enabled": True,
                "natural_tts_enabled": False,
                "max_context_tokens": 2048,
                "max_concurrent_requests": 2,
                "background_workers": False,
                "auto_unload_timeout": 300,
                "force_gc_interval": 60
            },
            "auto_detect": {
                "enabled": True,
                "min_ram_for_high_perf": 14.0,
                "safety_buffer_gb": 2.0
            }
        }
    
    def get_total_ram_gb(self) -> float:
        """Get total system RAM in GB"""
        return psutil.virtual_memory().total / (1024 ** 3)
    
    def auto_select_mode(self) -> str:
        """
        Automatically select performance mode based on RAM
        
        Returns:
            Selected mode name
        """
        total_ram = self.get_total_ram_gb()
        auto_config = self.config.get("auto_detect", {})
        min_ram_high = auto_config.get("min_ram_for_high_perf", 14.0)
        
        if total_ram >= min_ram_high:
            mode = "high_performance"
            logger.info(
                f"Auto-selected HIGH PERFORMANCE mode "
                f"(RAM: {total_ram:.1f}GB >= {min_ram_high:.1f}GB)"
            )
        else:
            mode = "low_power"
            logger.info(
                f"Auto-selected LOW POWER mode "
                f"(RAM: {total_ram:.1f}GB < {min_ram_high:.1f}GB)"
            )
        
        self.set_mode(mode)
        return mode
    
    def set_mode(self, mode_name: Literal["low_power", "high_performance"]):
        """
        Set performance mode
        
        Args:
            mode_name: Name of mode to set
        """
        mode_key = f"{mode_name}_mode"
        if mode_key not in self.config:
            logger.error(f"Mode not found: {mode_name}")
            return
        
        mode_config = self.config[mode_key]
        
        self.current_mode = PerformanceMode(
            name=mode_name,
            llm_model=mode_config.get("llm_model", "phi-3-mini-1.8b"),
            stt_model=mode_config.get("stt_model", "whisper-tiny"),
            tts_engine=mode_config.get("tts_engine", "pyttsx3"),
            vision_enabled=mode_config.get("vision_enabled", False),
            realtime_enabled=mode_config.get("realtime_enabled", True),
            natural_tts_enabled=mode_config.get("natural_tts_enabled", False),
            max_context_tokens=mode_config.get("max_context_tokens", 2048),
            max_concurrent_requests=mode_config.get("max_concurrent_requests", 2),
            background_workers=mode_config.get("background_workers", False),
            auto_unload_timeout=mode_config.get("auto_unload_timeout", 300),
            force_gc_interval=mode_config.get("force_gc_interval", 60),
            expected_ram_gb=self._estimate_ram_usage(mode_config)
        )
        
        logger.info(
            f"Performance mode set to: {mode_name.upper()} "
            f"(Expected RAM: {self.current_mode.expected_ram_gb:.1f}GB)"
        )
    
    def _estimate_ram_usage(self, mode_config: Dict) -> float:
        """Estimate RAM usage for mode"""
        # Base RAM estimates
        ram_estimates = {
            "phi-3-mini-1.8b": 2.0,
            "mistral-7b": 8.0,
            "llama-8b": 10.0,
            "whisper-tiny": 1.0,
            "whisper-base": 1.5,
            "whisper-small": 2.0,
            "pyttsx3": 0.1,
            "coqui-xtts": 0.5
        }
        
        total = 0.0
        total += ram_estimates.get(mode_config.get("llm_model", ""), 2.0)
        total += ram_estimates.get(mode_config.get("stt_model", ""), 1.0)
        total += ram_estimates.get(mode_config.get("tts_engine", ""), 0.1)
        
        if mode_config.get("vision_enabled", False):
            total += 1.5  # YOLOv8 + PaddleOCR
        
        return total
    
    def get_mode(self) -> PerformanceMode:
        """Get current performance mode"""
        return self.current_mode
    
    def get_recommendation(self) -> str:
        """Get recommended mode for current system"""
        total_ram = self.get_total_ram_gb()
        
        if total_ram >= 14.0:
            return "high_performance"
        else:
            return "low_power"


# Global performance manager
_global_manager: PerformanceManager = None


def get_performance_manager() -> PerformanceManager:
    """Get global performance manager"""
    global _global_manager
    if _global_manager is None:
        _global_manager = PerformanceManager()
    return _global_manager


if __name__ == "__main__":
    # Test performance manager
    print("Testing Performance Manager")
    print("=" * 50)
    
    manager = PerformanceManager()
    
    print(f"Total RAM: {manager.get_total_ram_gb():.1f}GB")
    print(f"Recommended mode: {manager.get_recommendation()}")
    print()
    
    mode = manager.get_mode()
    print(f"Current Mode: {mode.name.upper()}")
    print(f"  LLM: {mode.llm_model}")
    print(f"  STT: {mode.stt_model}")
    print(f"  TTS: {mode.tts_engine}")
    print(f"  Vision: {mode.vision_enabled}")
    print(f"  Expected RAM: {mode.expected_ram_gb:.1f}GB")
    print("=" * 50)
