"""
Hardware Capability Detection
Analyzes system hardware to recommend optimal configurations
"""

import psutil
import platform
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from core.structured_logger import get_structured_logger

@dataclass
class SystemProfile:
    """System hardware profile"""
    cpu_cores_physical: int
    cpu_cores_logical: int
    ram_total_gb: float
    ram_available_gb: float
    gpu_available: bool
    gpu_name: Optional[str]
    gpu_vram_gb: float
    gpu_cuda_cores: int
    gpu_compute_capability: Optional[str]
    os_platform: str
    python_version: str

class HardwareDetector:
    """
    Analyzes system hardware to inform auto-configuration
    
    Features:
    - Detect GPU VRAM, CUDA cores (if torch available)
    - Detect CPU cores and RAM
    - Recommend quantization levels based on hardware
    """
    
    def __init__(self):
        self.struct_logger = get_structured_logger("HardwareDetector")
        self._profile: Optional[SystemProfile] = None

    def analyze_system(self) -> SystemProfile:
        """
        Analyze system hardware and return profile
        
        Returns:
            SystemProfile object
        """
        if self._profile:
            return self._profile
            
        try:
            # CPU & RAM
            cpu_physical = psutil.cpu_count(logical=False) or 1
            cpu_logical = psutil.cpu_count(logical=True) or 1
            
            mem = psutil.virtual_memory()
            ram_total = round(mem.total / (1024**3), 2)
            ram_available = round(mem.available / (1024**3), 2)
            
            # GPU Detection
            gpu_available = False
            gpu_name = None
            gpu_vram = 0.0
            gpu_cuda_cores = 0
            gpu_compute = None
            
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_available = True
                    gpu_name = torch.cuda.get_device_name(0)
                    # VRAM in GB
                    props = torch.cuda.get_device_properties(0)
                    gpu_vram = round(props.total_memory / (1024**3), 2)
                    gpu_compute = f"{props.major}.{props.minor}"
                    # CUDA cores estimation (approximate based on SMs, varies by arch)
                    # This is just a rough heuristic or placeholder
                    gpu_cuda_cores = getattr(props, 'multi_processor_count', 0) * 64 
            except ImportError:
                self.struct_logger.debug("torch_import_failed", "PyTorch not installed, skipping GPU details")
            except Exception as e:
                self.struct_logger.warning("gpu_detect_failed", f"GPU detection failed: {e}")

            self._profile = SystemProfile(
                cpu_cores_physical=cpu_physical,
                cpu_cores_logical=cpu_logical,
                ram_total_gb=ram_total,
                ram_available_gb=ram_available,
                gpu_available=gpu_available,
                gpu_name=gpu_name,
                gpu_vram_gb=gpu_vram,
                gpu_cuda_cores=gpu_cuda_cores,
                gpu_compute_capability=gpu_compute,
                os_platform=platform.system(),
                python_version=platform.python_version()
            )
            
            self.struct_logger.info(
                "system_analyzed",
                "System hardware analysis complete",
                profile=self._profile.__dict__
            )
            
            return self._profile
            
        except Exception as e:
            self.struct_logger.error("analysis_failed", f"System analysis failed: {e}")
            # Return safe fallback
            return SystemProfile(
                cpu_cores_physical=1,
                cpu_cores_logical=1,
                ram_total_gb=4.0,
                ram_available_gb=2.0,
                gpu_available=False,
                gpu_name=None,
                gpu_vram_gb=0.0,
                gpu_cuda_cores=0,
                gpu_compute_capability=None,
                os_platform=platform.system(),
                python_version=platform.python_version()
            )

    def recommend_quantization(self, model_size_gb: float) -> str:
        """
        Recommend optimal quantization based on available hardware
        
        Args:
            model_size_gb: Estimated size of the model in GB (FP16)
            
        Returns:
            Recommended quantization string (e.g., "Q4_K_M", "Q8_0", "F16")
        """
        profile = self.analyze_system()
        
        # Determine available memory (VRAM if GPU, else RAM)
        if profile.gpu_available:
            available_mem = profile.gpu_vram_gb * 0.9  # Leave 10% headroom
            device = "GPU"
        else:
            available_mem = profile.ram_available_gb * 0.8  # Leave 20% headroom for OS
            device = "CPU"
            
        # Heuristic logic
        # FP16 size is baseline.
        # Q8 ~ 55% of FP16
        # Q6 ~ 45%
        # Q5 ~ 40%
        # Q4 ~ 35%
        # Q3 ~ 30%
        # Q2 ~ 25%
        
        if available_mem >= model_size_gb:
            rec = "F16" if device == "GPU" else "Q8_0" # CPU usually prefers quantized for speed
        elif available_mem >= model_size_gb * 0.55:
            rec = "Q8_0"
        elif available_mem >= model_size_gb * 0.45:
            rec = "Q6_K"
        elif available_mem >= model_size_gb * 0.40:
            rec = "Q5_K_M"
        elif available_mem >= model_size_gb * 0.35:
            rec = "Q4_K_M"
        elif available_mem >= model_size_gb * 0.30:
            rec = "Q3_K_M"
        else:
            rec = "Q2_K" # Desperate measure
            
        self.struct_logger.info(
            "quantization_recommended",
            f"Recommended {rec} for {model_size_gb}GB model on {device}",
            available_mem_gb=available_mem,
            recommendation=rec
        )
        
        return rec

# Singleton
_hardware_detector: Optional[HardwareDetector] = None

def get_hardware_detector() -> HardwareDetector:
    global _hardware_detector
    if _hardware_detector is None:
        _hardware_detector = HardwareDetector()
    return _hardware_detector
