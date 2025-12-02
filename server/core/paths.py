"""
Cross-Platform Path Management
Provides platform-specific directories for clean installation
"""

import os
import platform
from pathlib import Path
from typing import Optional


def get_app_data_dir() -> Path:
    """
    Get platform-specific application data directory
    
    Returns:
        Path to LyraAI data directory:
        - Windows: %APPDATA%/LyraAI
        - macOS: ~/Library/Application Support/LyraAI
        - Linux: ~/.local/share/LyraAI
    """
    system = platform.system()
    
    if system == "Windows":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData/Roaming"))
    elif system == "Darwin":  # macOS
        base = Path.home() / "Library/Application Support"
    else:  # Linux and others
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share"))
    
    app_dir = base / "LyraAI"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_models_dir() -> Path:
    """Get models directory"""
    models_dir = get_app_data_dir() / "models"
    models_dir.mkdir(exist_ok=True)
    return models_dir


def get_logs_dir() -> Path:
    """Get logs directory"""
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_cache_dir() -> Path:
    """Get cache directory (for temporary files)"""
    cache_dir = get_app_data_dir() / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def get_config_dir() -> Path:
    """Get config directory"""
    config_dir = get_app_data_dir() / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """Get data directory (for reminders, memory, etc.)"""
    data_dir = get_app_data_dir() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_project_root() -> Path:
    """Get project root directory (where ai-worker/ is located)"""
    return Path(__file__).parent.parent.parent


def get_local_models_dir() -> Path:
    """Get local models directory (in project, for development)"""
    local_models = get_project_root() / "ai-worker" / "models"
    local_models.mkdir(exist_ok=True)
    return local_models


# Initialize all directories on import
def init_directories():
    """Initialize all required directories"""
    get_app_data_dir()
    get_models_dir()
    get_logs_dir()
    get_cache_dir()
    get_config_dir()
    get_data_dir()


if __name__ == "__main__":
    # Test and display paths
    print("Lyra AI Mark2 - Directory Structure")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print(f"App Data: {get_app_data_dir()}")
    print(f"Models: {get_models_dir()}")
    print(f"Logs: {get_logs_dir()}")
    print(f"Cache: {get_cache_dir()}")
    print(f"Config: {get_config_dir()}")
    print(f"Data: {get_data_dir()}")
    print(f"Project Root: {get_project_root()}")
    print("=" * 50)
