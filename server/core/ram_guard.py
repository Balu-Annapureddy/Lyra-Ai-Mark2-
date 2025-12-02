"""
RAM Guard - Task-Time Memory Validation
Prevents system crashes by checking RAM before model operations
"""

import psutil
import logging
from typing import Literal, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Model types with their RAM requirements"""
    WHISPER_TINY = "whisper-tiny"
    WHISPER_BASE = "whisper-base"
    WHISPER_SMALL = "whisper-small"
    PHI3_MINI = "phi-3-mini"
    MISTRAL_7B = "mistral-7b"
    LLAMA_8B = "llama-8b"
    COQUI_TTS = "coqui-tts"
    YOLOV8 = "yolov8"
    PADDLEOCR = "paddleocr"


# RAM requirements in GB
RAM_REQUIREMENTS: Dict[ModelType, float] = {
    ModelType.WHISPER_TINY: 1.0,
    ModelType.WHISPER_BASE: 1.5,
    ModelType.WHISPER_SMALL: 2.0,
    ModelType.PHI3_MINI: 2.0,
    ModelType.MISTRAL_7B: 8.0,
    ModelType.LLAMA_8B: 10.0,
    ModelType.COQUI_TTS: 0.5,
    ModelType.YOLOV8: 1.0,
    ModelType.PADDLEOCR: 0.5,
}


def get_available_ram_gb() -> float:
    """
    Get available RAM in GB
    
    Returns:
        Available RAM in gigabytes
    """
    mem = psutil.virtual_memory()
    return mem.available / (1024 ** 3)


def get_total_ram_gb() -> float:
    """
    Get total RAM in GB
    
    Returns:
        Total RAM in gigabytes
    """
    mem = psutil.virtual_memory()
    return mem.total / (1024 ** 3)


def get_ram_usage_percent() -> float:
    """
    Get current RAM usage percentage
    
    Returns:
        RAM usage percentage (0-100)
    """
    mem = psutil.virtual_memory()
    return mem.percent


def check_ram_before_task(
    model_type: ModelType,
    task_name: str = "model_operation"
) -> Literal["local", "cloud", "deny"]:
    """
    Check if sufficient RAM is available before loading a model
    
    Args:
        model_type: Type of model to load
        task_name: Name of the task (for logging)
    
    Returns:
        "local" if sufficient RAM available
        "cloud" if should fallback to cloud
        "deny" if operation should be denied
    """
    required_ram = RAM_REQUIREMENTS.get(model_type, 2.0)
    available_ram = get_available_ram_gb()
    ram_percent = get_ram_usage_percent()
    
    logger.info(
        f"RAM Check for {task_name}: "
        f"Required={required_ram:.1f}GB, "
        f"Available={available_ram:.1f}GB, "
        f"Usage={ram_percent:.1f}%"
    )
    
    # Critical: RAM usage > 90%
    if ram_percent > 90:
        logger.warning(
            f"RAM usage critical ({ram_percent:.1f}%). "
            f"Forcing cloud mode for {task_name}"
        )
        return "cloud"
    
    # Insufficient RAM for model
    if available_ram < required_ram:
        logger.warning(
            f"{task_name} requires {required_ram:.1f}GB, "
            f"only {available_ram:.1f}GB available. "
            f"Falling back to cloud."
        )
        return "cloud"
    
    # Sufficient RAM but tight (< 2GB buffer)
    if available_ram < required_ram + 2.0:
        logger.info(
            f"RAM tight for {task_name}. "
            f"Proceeding locally but monitoring closely."
        )
    
    return "local"


def can_load_model(model_type: ModelType) -> bool:
    """
    Quick check if model can be loaded
    
    Args:
        model_type: Type of model
    
    Returns:
        True if model can be loaded, False otherwise
    """
    decision = check_ram_before_task(model_type, f"load_{model_type.value}")
    return decision == "local"


def get_ram_status() -> Dict[str, any]:
    """
    Get comprehensive RAM status
    
    Returns:
        Dictionary with RAM statistics
    """
    mem = psutil.virtual_memory()
    return {
        "total_gb": mem.total / (1024 ** 3),
        "available_gb": mem.available / (1024 ** 3),
        "used_gb": mem.used / (1024 ** 3),
        "percent": mem.percent,
        "status": "critical" if mem.percent > 90 else "warning" if mem.percent > 75 else "ok"
    }


if __name__ == "__main__":
    # Test RAM guard
    print("Lyra AI - RAM Guard Test")
    print("=" * 50)
    
    status = get_ram_status()
    print(f"Total RAM: {status['total_gb']:.1f}GB")
    print(f"Available RAM: {status['available_gb']:.1f}GB")
    print(f"Used RAM: {status['used_gb']:.1f}GB")
    print(f"Usage: {status['percent']:.1f}%")
    print(f"Status: {status['status']}")
    print()
    
    # Test model checks
    models_to_test = [
        ModelType.WHISPER_TINY,
        ModelType.PHI3_MINI,
        ModelType.MISTRAL_7B,
    ]
    
    for model in models_to_test:
        decision = check_ram_before_task(model, f"test_{model.value}")
        print(f"{model.value}: {decision}")
