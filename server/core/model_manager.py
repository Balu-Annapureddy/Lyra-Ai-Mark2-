"""
Model Manager - Download, Verify, and Manage AI Models
Integrates with lazy loader, warmup, and safety systems
"""

import logging
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
import aiohttp
from tqdm import tqdm

from core.paths import get_models_dir
from core.lazy_loader import get_lazy_loader
from core.warmup import get_warmer
from core.ram_guard import ModelType, can_load_model
from core.safety import safe_model_operation

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Model information"""
    id: str
    name: str
    type: str  # "llm", "stt", "tts", "vision"
    size_mb: int
    ram_required_mb: int
    url: str
    sha256: str
    filename: str
    description: str
    installed: bool = False


# Model Registry with SHA256 checksums
MODEL_REGISTRY: Dict[str, ModelInfo] = {
    "phi-3-mini": ModelInfo(
        id="phi-3-mini",
        name="Phi-3 Mini 1.8B Q4",
        type="llm",
        size_mb=1200,
        ram_required_mb=2000,
        url="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
        sha256="",  # Add actual SHA256
        filename="phi-3-mini-q4.gguf",
        description="Lightweight LLM for 8GB RAM systems"
    ),
    "whisper-tiny": ModelInfo(
        id="whisper-tiny",
        name="Whisper Tiny",
        type="stt",
        size_mb=40,
        ram_required_mb=1000,
        url="",  # faster-whisper downloads automatically
        sha256="",
        filename="whisper-tiny",
        description="Lightweight STT model"
    ),
    "whisper-base": ModelInfo(
        id="whisper-base",
        name="Whisper Base",
        type="stt",
        size_mb=140,
        ram_required_mb=1500,
        url="",
        sha256="",
        filename="whisper-base",
        description="Better accuracy STT model"
    ),
}


class ModelManager:
    """
    Manages AI model downloads, verification, and lifecycle
    Integrates with lazy loader and safety systems
    """
    
    def __init__(self):
        """Initialize model manager"""
        self.models_dir = get_models_dir()
        self.registry = MODEL_REGISTRY
        self.lazy_loader = get_lazy_loader()
        self.warmer = get_warmer()
        logger.info(f"ModelManager initialized: {self.models_dir}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models
        
        Returns:
            List of model information dictionaries
        """
        models = []
        for model_id, info in self.registry.items():
            model_path = self.models_dir / info.filename
            installed = model_path.exists()
            
            models.append({
                "id": info.id,
                "name": info.name,
                "type": info.type,
                "size_mb": info.size_mb,
                "ram_required_mb": info.ram_required_mb,
                "description": info.description,
                "installed": installed,
                "can_load": can_load_model(ModelType(info.id)) if installed else False
            })
        
        return models
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get model information by ID"""
        return self.registry.get(model_id)
    
    def is_installed(self, model_id: str) -> bool:
        """Check if model is installed"""
        info = self.get_model_info(model_id)
        if not info:
            return False
        
        model_path = self.models_dir / info.filename
        return model_path.exists()
    
    async def download_model(
        self,
        model_id: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Download and verify model
        
        Args:
            model_id: Model identifier
            progress_callback: Optional callback(downloaded_mb, total_mb)
        
        Returns:
            Result dictionary with success status
        """
        info = self.get_model_info(model_id)
        if not info:
            return {
                "success": False,
                "error": f"Model not found: {model_id}"
            }
        
        if self.is_installed(model_id):
            return {
                "success": True,
                "message": "Model already installed",
                "path": str(self.models_dir / info.filename)
            }
        
        logger.info(f"Downloading model: {info.name}")
        
        # Check if URL is provided
        if not info.url:
            return {
                "success": False,
                "error": f"No download URL for {model_id}"
            }
        
        model_path = self.models_dir / info.filename
        
        # Download with retry logic (3 attempts)
        for attempt in range(3):
            try:
                logger.info(f"Download attempt {attempt + 1}/3")
                
                await self._download_file(
                    info.url,
                    model_path,
                    progress_callback
                )
                
                # Verify SHA256 if provided
                if info.sha256:
                    logger.info("Verifying SHA256...")
                    actual_sha256 = self._calculate_sha256(model_path)
                    
                    if actual_sha256 != info.sha256:
                        logger.error(f"SHA256 mismatch: {actual_sha256} != {info.sha256}")
                        model_path.unlink()  # Delete corrupted file
                        
                        if attempt < 2:
                            logger.warning("Retrying download...")
                            continue
                        else:
                            return {
                                "success": False,
                                "error": "SHA256 verification failed after 3 attempts"
                            }
                
                logger.info(f"Model downloaded successfully: {info.name}")
                
                return {
                    "success": True,
                    "path": str(model_path),
                    "size_mb": model_path.stat().st_size // (1024 ** 2)
                }
            
            except Exception as e:
                logger.error(f"Download attempt {attempt + 1} failed: {e}")
                
                if model_path.exists():
                    model_path.unlink()
                
                if attempt < 2:
                    await asyncio.sleep(2)  # Wait before retry
                else:
                    return {
                        "success": False,
                        "error": f"Download failed after 3 attempts: {str(e)}"
                    }
    
    async def _download_file(
        self,
        url: str,
        dest_path: Path,
        progress_callback: Optional[callable] = None
    ):
        """Download file with progress tracking"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(dest_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress_callback(
                                downloaded // (1024 ** 2),
                                total_size // (1024 ** 2)
                            )
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def delete_model(self, model_id: str) -> Dict[str, Any]:
        """
        Delete installed model
        
        Args:
            model_id: Model identifier
        
        Returns:
            Result dictionary
        """
        info = self.get_model_info(model_id)
        if not info:
            return {
                "success": False,
                "error": f"Model not found: {model_id}"
            }
        
        model_path = self.models_dir / info.filename
        
        if not model_path.exists():
            return {
                "success": False,
                "error": "Model not installed"
            }
        
        try:
            # Unload from lazy loader first
            self.lazy_loader.unload_model(model_id)
            
            # Delete file
            model_path.unlink()
            logger.info(f"Deleted model: {info.name}")
            
            return {
                "success": True,
                "message": f"Deleted {info.name}"
            }
        
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_installed_models(self) -> List[str]:
        """Get list of installed model IDs"""
        return [
            model_id
            for model_id in self.registry.keys()
            if self.is_installed(model_id)
        ]
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics"""
        total_size = 0
        
        for model_id, info in self.registry.items():
            model_path = self.models_dir / info.filename
            if model_path.exists():
                total_size += model_path.stat().st_size
        
        return {
            "total_mb": total_size // (1024 ** 2),
            "models_count": len(self.get_installed_models()),
            "models_dir": str(self.models_dir)
        }


# Global model manager instance
_global_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get global model manager instance"""
    global _global_model_manager
    if _global_model_manager is None:
        _global_model_manager = ModelManager()
    return _global_model_manager


if __name__ == "__main__":
    # Test model manager
    print("Testing Model Manager")
    print("=" * 50)
    
    manager = ModelManager()
    
    models = manager.list_models()
    print(f"Available models: {len(models)}")
    for model in models:
        print(f"  - {model['name']}: {model['size_mb']}MB (installed: {model['installed']})")
    
    print()
    usage = manager.get_disk_usage()
    print(f"Disk usage: {usage['total_mb']}MB ({usage['models_count']} models)")
    print("=" * 50)
