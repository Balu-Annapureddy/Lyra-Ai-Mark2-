"""
GPU Manager - Hardware Detection and GPU Support
Detects NVIDIA CUDA, AMD ROCm/OpenCL, and manages GPU resources
"""

import logging
import platform
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
import psutil

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU information"""
    type: Literal["nvidia", "amd", "intel", "none"]
    name: str
    memory_total_mb: Optional[int]
    memory_available_mb: Optional[int]
    compute_capability: Optional[str]
    driver_version: Optional[str]
    available: bool


class GPUManager:
    """
    Manages GPU detection and resource allocation
    Supports NVIDIA CUDA, AMD ROCm/OpenCL, and Intel
    """
    
    def __init__(self):
        """Initialize GPU manager"""
        self._gpu_info: Optional[GPUInfo] = None
        self._detected = False
        logger.info("GPUManager initialized")
    
    def detect_gpu(self) -> GPUInfo:
        """
        Detect available GPU
        
        Returns:
            GPUInfo with detected GPU details
        """
        if self._detected:
            return self._gpu_info
        
        logger.info("Detecting GPU...")
        
        # Try NVIDIA CUDA first
        nvidia_info = self._detect_nvidia()
        if nvidia_info.available:
            self._gpu_info = nvidia_info
            self._detected = True
            logger.info(f"Detected NVIDIA GPU: {nvidia_info.name}")
            return nvidia_info
        
        # Try AMD ROCm/OpenCL
        amd_info = self._detect_amd()
        if amd_info.available:
            self._gpu_info = amd_info
            self._detected = True
            logger.info(f"Detected AMD GPU: {amd_info.name}")
            return amd_info
        
        # Try Intel
        intel_info = self._detect_intel()
        if intel_info.available:
            self._gpu_info = intel_info
            self._detected = True
            logger.info(f"Detected Intel GPU: {intel_info.name}")
            return intel_info
        
        # No GPU found
        no_gpu = GPUInfo(
            type="none",
            name="CPU Only",
            memory_total_mb=None,
            memory_available_mb=None,
            compute_capability=None,
            driver_version=None,
            available=False
        )
        self._gpu_info = no_gpu
        self._detected = True
        logger.info("No GPU detected, using CPU only")
        return no_gpu
    
    def _detect_nvidia(self) -> GPUInfo:
        """Detect NVIDIA CUDA GPU"""
        try:
            import torch
            
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                if device_count > 0:
                    # Get first GPU
                    name = torch.cuda.get_device_name(0)
                    props = torch.cuda.get_device_properties(0)
                    
                    return GPUInfo(
                        type="nvidia",
                        name=name,
                        memory_total_mb=props.total_memory // (1024 ** 2),
                        memory_available_mb=self._get_nvidia_free_memory(),
                        compute_capability=f"{props.major}.{props.minor}",
                        driver_version=torch.version.cuda,
                        available=True
                    )
        except Exception as e:
            logger.debug(f"NVIDIA detection failed: {e}")
        
        return GPUInfo(
            type="nvidia",
            name="Not Available",
            memory_total_mb=None,
            memory_available_mb=None,
            compute_capability=None,
            driver_version=None,
            available=False
        )
    
    def _detect_amd(self) -> GPUInfo:
        """Detect AMD ROCm/OpenCL GPU"""
        try:
            import pyopencl as cl
            
            platforms = cl.get_platforms()
            for platform in platforms:
                devices = platform.get_devices(device_type=cl.device_type.GPU)
                for device in devices:
                    vendor = device.vendor.lower()
                    if "amd" in vendor or "advanced micro devices" in vendor:
                        name = device.name
                        memory_mb = device.global_mem_size // (1024 ** 2)
                        
                        return GPUInfo(
                            type="amd",
                            name=name,
                            memory_total_mb=memory_mb,
                            memory_available_mb=memory_mb,  # OpenCL doesn't provide free memory
                            compute_capability=device.version,
                            driver_version=device.driver_version,
                            available=True
                        )
        except Exception as e:
            logger.debug(f"AMD detection failed: {e}")
        
        return GPUInfo(
            type="amd",
            name="Not Available",
            memory_total_mb=None,
            memory_available_mb=None,
            compute_capability=None,
            driver_version=None,
            available=False
        )
    
    def _detect_intel(self) -> GPUInfo:
        """Detect Intel GPU"""
        try:
            import pyopencl as cl
            
            platforms = cl.get_platforms()
            for platform in platforms:
                devices = platform.get_devices(device_type=cl.device_type.GPU)
                for device in devices:
                    vendor = device.vendor.lower()
                    if "intel" in vendor:
                        name = device.name
                        memory_mb = device.global_mem_size // (1024 ** 2)
                        
                        return GPUInfo(
                            type="intel",
                            name=name,
                            memory_total_mb=memory_mb,
                            memory_available_mb=memory_mb,
                            compute_capability=device.version,
                            driver_version=device.driver_version,
                            available=True
                        )
        except Exception as e:
            logger.debug(f"Intel detection failed: {e}")
        
        return GPUInfo(
            type="intel",
            name="Not Available",
            memory_total_mb=None,
            memory_available_mb=None,
            compute_capability=None,
            driver_version=None,
            available=False
        )
    
    def _get_nvidia_free_memory(self) -> Optional[int]:
        """Get free NVIDIA GPU memory in MB"""
        try:
            import torch
            if torch.cuda.is_available():
                free_memory = torch.cuda.mem_get_info()[0]
                return free_memory // (1024 ** 2)
        except:
            pass
        return None
    
    def get_gpu_info(self) -> GPUInfo:
        """Get GPU information (cached)"""
        if not self._detected:
            return self.detect_gpu()
        return self._gpu_info
    
    def has_gpu(self) -> bool:
        """Check if GPU is available"""
        info = self.get_gpu_info()
        return info.available
    
    def get_recommended_backend(self) -> Literal["cuda", "opencl", "cpu"]:
        """
        Get recommended backend for model inference
        
        Returns:
            "cuda" for NVIDIA, "opencl" for AMD/Intel, "cpu" for no GPU
        """
        info = self.get_gpu_info()
        
        if info.type == "nvidia":
            return "cuda"
        elif info.type in ["amd", "intel"]:
            return "opencl"
        else:
            return "cpu"
    
    def get_llama_cpp_args(self) -> Dict[str, Any]:
        """
        Get llama-cpp-python initialization arguments based on GPU
        
        Returns:
            Dictionary with n_gpu_layers and other GPU-specific args
        """
        info = self.get_gpu_info()
        
        if info.type == "nvidia":
            # NVIDIA CUDA
            return {
                "n_gpu_layers": -1,  # Offload all layers
                "n_ctx": 4096,
                "n_batch": 512,
                "use_mlock": True
            }
        elif info.type == "amd":
            # AMD OpenCL (via CLBlast)
            return {
                "n_gpu_layers": -1,
                "n_ctx": 4096,
                "n_batch": 512,
                "use_mlock": True,
                # Note: Requires llama-cpp-python built with CLBlast
            }
        else:
            # CPU only
            return {
                "n_gpu_layers": 0,
                "n_ctx": 2048,
                "n_batch": 256,
                "n_threads": psutil.cpu_count(logical=False) or 4
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive GPU status"""
        info = self.get_gpu_info()
        
        return {
            "gpu_available": info.available,
            "gpu_type": info.type,
            "gpu_name": info.name,
            "memory_total_mb": info.memory_total_mb,
            "memory_available_mb": info.memory_available_mb,
            "compute_capability": info.compute_capability,
            "driver_version": info.driver_version,
            "recommended_backend": self.get_recommended_backend(),
            "platform": platform.system()
        }
    
    def run_self_test(self) -> Dict[str, Any]:
        """
        Run GPU self-test to verify functionality
        
        Returns:
            Test results dictionary
        """
        logger.info("Running GPU self-test...")
        
        info = self.get_gpu_info()
        results = {
            "gpu_detected": info.available,
            "gpu_type": info.type,
            "tests_passed": [],
            "tests_failed": [],
            "warnings": []
        }
        
        if not info.available:
            results["warnings"].append("No GPU detected, using CPU only")
            return results
        
        # Test 1: Memory availability
        if info.memory_total_mb and info.memory_total_mb > 0:
            results["tests_passed"].append("memory_detection")
        else:
            results["tests_failed"].append("memory_detection")
        
        # Test 2: Driver version
        if info.driver_version:
            results["tests_passed"].append("driver_detection")
        else:
            results["tests_failed"].append("driver_detection")
        
        # Test 3: NVIDIA-specific tests
        if info.type == "nvidia":
            try:
                import torch
                if torch.cuda.is_available():
                    # Try simple tensor operation
                    test_tensor = torch.zeros(100, 100).cuda()
                    result = test_tensor.sum().item()
                    results["tests_passed"].append("nvidia_tensor_ops")
                else:
                    results["tests_failed"].append("nvidia_cuda_unavailable")
            except Exception as e:
                results["tests_failed"].append(f"nvidia_test: {str(e)}")
        
        # Test 4: AMD/OpenCL tests
        elif info.type in ["amd", "intel"]:
            try:
                import pyopencl as cl
                platforms = cl.get_platforms()
                if platforms:
                    results["tests_passed"].append("opencl_platform_detection")
                else:
                    results["tests_failed"].append("opencl_no_platforms")
            except Exception as e:
                results["tests_failed"].append(f"opencl_test: {str(e)}")
        
        # Windows AMD fallback check
        if platform.system() == "Windows" and info.type == "amd":
            if not info.available:
                results["warnings"].append(
                    "AMD GPU on Windows: Consider using CPU mode for stability"
                )
        
        logger.info(f"Self-test complete: {len(results['tests_passed'])} passed, {len(results['tests_failed'])} failed")
        
        return results
    
    def stress_test_vram(self, duration_seconds: int = 5) -> Dict[str, Any]:
        """
        Run VRAM stress test
        
        Args:
            duration_seconds: Test duration
        
        Returns:
            Stress test results
        """
        logger.info(f"Running VRAM stress test ({duration_seconds}s)...")
        
        info = self.get_gpu_info()
        results = {
            "success": False,
            "gpu_type": info.type,
            "peak_usage_mb": 0,
            "errors": []
        }
        
        if not info.available or info.type == "none":
            results["errors"].append("No GPU available for stress test")
            return results
        
        try:
            if info.type == "nvidia":
                import torch
                import time
                
                # Allocate tensors to stress VRAM
                tensors = []
                start_time = time.time()
                
                while time.time() - start_time < duration_seconds:
                    try:
                        # Allocate 100MB tensor
                        tensor = torch.zeros(100 * 1024 * 1024 // 4).cuda()  # 100MB
                        tensors.append(tensor)
                        
                        # Check memory usage
                        allocated = torch.cuda.memory_allocated() // (1024 ** 2)
                        results["peak_usage_mb"] = max(results["peak_usage_mb"], allocated)
                        
                        time.sleep(0.1)
                    except RuntimeError as e:
                        if "out of memory" in str(e).lower():
                            logger.info("Reached VRAM limit")
                            break
                        raise
                
                # Cleanup
                tensors.clear()
                torch.cuda.empty_cache()
                
                results["success"] = True
                logger.info(f"Stress test complete: Peak usage {results['peak_usage_mb']}MB")
            
            else:
                results["errors"].append(f"Stress test not implemented for {info.type}")
        
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Stress test failed: {e}")
        
        return results


# Global GPU manager instance
_global_gpu_manager: Optional[GPUManager] = None


def get_gpu_manager() -> GPUManager:
    """Get global GPU manager instance"""
    global _global_gpu_manager
    if _global_gpu_manager is None:
        _global_gpu_manager = GPUManager()
    return _global_gpu_manager


if __name__ == "__main__":
    # Test GPU manager
    print("Testing GPU Manager")
    print("=" * 50)
    
    manager = GPUManager()
    status = manager.get_status()
    
    print(f"GPU Available: {status['gpu_available']}")
    print(f"GPU Type: {status['gpu_type']}")
    print(f"GPU Name: {status['gpu_name']}")
    print(f"Memory: {status['memory_total_mb']}MB total")
    print(f"Recommended Backend: {status['recommended_backend']}")
    print()
    
    print("Llama.cpp Args:")
    print(manager.get_llama_cpp_args())
    print("=" * 50)
