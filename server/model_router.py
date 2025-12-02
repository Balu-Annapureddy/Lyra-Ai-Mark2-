"""
Model Router - Intelligent model selection based on hardware and user preferences
Supports: offline-mini, offline-big, hybrid, cloud modes
"""

import os
import platform
import psutil
import logging
from typing import Dict, Optional, List
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelMode(str, Enum):
    """Available model modes"""
    OFFLINE_MINI = "offline-mini"
    OFFLINE_BIG = "offline-big"
    HYBRID = "hybrid"
    CLOUD = "cloud"

class ModelRouter:
    """
    Routes LLM queries to appropriate model based on:
    - Hardware capabilities (RAM, GPU)
    - User preferences (offline/hybrid/cloud)
    - Model availability
    """
    
    def __init__(self):
        self.models_dir = Path(__file__).parent / "models"
        self.models_dir.mkdir(exist_ok=True)
        
        # Hardware info
        self.hardware_info = self.detect_hardware()
        
        # Available models
        self.available_models = self._scan_available_models()
        
        logger.info(f"Model Router initialized. Available models: {self.available_models}")
    
    def detect_hardware(self) -> Dict:
        """
        Detect system hardware capabilities
        Returns: dict with RAM, GPU info
        """
        try:
            # RAM detection
            ram_bytes = psutil.virtual_memory().total
            ram_gb = ram_bytes / (1024 ** 3)
            
            # GPU detection (basic check)
            has_gpu = False
            gpu_name = "None"
            
            try:
                # Try to detect NVIDIA GPU
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    has_gpu = True
                    gpu_name = result.stdout.strip()
            except:
                pass
            
            return {
                "ram_gb": ram_gb,
                "has_gpu": has_gpu,
                "gpu_name": gpu_name,
                "platform": platform.system(),
                "cpu_count": psutil.cpu_count()
            }
        except Exception as e:
            logger.error(f"Hardware detection error: {e}")
            return {
                "ram_gb": 8.0,  # Default assumption
                "has_gpu": False,
                "gpu_name": "None",
                "platform": platform.system(),
                "cpu_count": 4
            }
    
    def _scan_available_models(self) -> Dict[str, Optional[str]]:
        """
        Scan models directory for available GGUF files
        Returns: dict mapping model tier to file path
        """
        models = {
            "mini": None,
            "big": None
        }
        
        # Look for model files
        if self.models_dir.exists():
            for file in self.models_dir.glob("*.gguf"):
                filename = file.name.lower()
                
                # Detect mini models (1-3B)
                if any(x in filename for x in ["mini", "1b", "2b", "3b", "tiny", "small"]):
                    models["mini"] = str(file)
                
                # Detect big models (7B+)
                elif any(x in filename for x in ["7b", "13b", "20b", "70b", "big", "large"]):
                    models["big"] = str(file)
        
        return models
    
    def select_model(self, mode: str = "hybrid") -> Dict:
        """
        Select appropriate model based on mode and hardware
        
        Args:
            mode: offline-mini, offline-big, hybrid, cloud
        
        Returns:
            dict with model info and selected tier
        """
        mode = mode.lower()
        
        # Cloud mode - always use cloud API
        if mode == "cloud":
            return {
                "tier": "cloud",
                "model_path": None,
                "model_name": "gemini-1.5-flash",  # Default cloud model
                "requires_api": True
            }
        
        # Offline-mini mode
        if mode == "offline-mini":
            if self.available_models["mini"]:
                return {
                    "tier": "offline-mini",
                    "model_path": self.available_models["mini"],
                    "model_name": "local-mini",
                    "requires_api": False
                }
            else:
                logger.warning("Mini model not found, using stub response")
                return {
                    "tier": "stub",
                    "model_path": None,
                    "model_name": "stub",
                    "requires_api": False
                }
        
        # Offline-big mode
        if mode == "offline-big":
            # Check if hardware can handle big model
            if self.hardware_info["ram_gb"] < 16:
                logger.warning("Insufficient RAM for big model, falling back to mini")
                return self.select_model("offline-mini")
            
            if self.available_models["big"]:
                return {
                    "tier": "offline-big",
                    "model_path": self.available_models["big"],
                    "model_name": "local-big",
                    "requires_api": False
                }
            else:
                logger.warning("Big model not found, falling back to mini")
                return self.select_model("offline-mini")
        
        # Hybrid mode (default)
        if mode == "hybrid":
            # Try local first, fallback to cloud
            if self.available_models["mini"]:
                return self.select_model("offline-mini")
            elif self.available_models["big"] and self.hardware_info["ram_gb"] >= 16:
                return self.select_model("offline-big")
            else:
                logger.info("No local models available, using cloud")
                return self.select_model("cloud")
        
        # Default fallback
        return self.select_model("cloud")
    
    async def route_query(
        self,
        query: str,
        mode: str = "hybrid",
        context: Optional[List] = None
    ) -> Dict:
        """
        Route query to selected model and return response
        
        Args:
            query: User query text
            mode: Model mode (offline-mini/offline-big/hybrid/cloud)
            context: Optional conversation context
        
        Returns:
            dict with response text, model used, and mode
        """
        # Select model
        model_info = self.select_model(mode)
        
        # Route to appropriate handler
        if model_info["tier"] == "cloud":
            response = await self._query_cloud(query, context)
        elif model_info["tier"] in ["offline-mini", "offline-big"]:
            response = await self._query_local(query, model_info, context)
        else:
            # Stub response
            response = await self._query_stub(query)
        
        return {
            "text": response,
            "model": model_info["model_name"],
            "mode": model_info["tier"]
        }
    
    async def _query_local(
        self,
        query: str,
        model_info: Dict,
        context: Optional[List] = None
    ) -> str:
        """
        Query local GGUF model using llama-cpp-python
        
        TODO: Implement llama-cpp-python integration
        For now, returns stub response
        """
        logger.info(f"Querying local model: {model_info['model_name']}")
        
        # TODO: Load and query GGUF model
        # from llama_cpp import Llama
        # llm = Llama(model_path=model_info["model_path"])
        # response = llm(query, max_tokens=256)
        
        # Stub response for now
        return f"[Local Model Response] I received your query: '{query}'. Local model integration is ready for implementation."
    
    async def _query_cloud(
        self,
        query: str,
        context: Optional[List] = None
    ) -> str:
        """
        Query cloud API (Gemini or OpenAI)
        
        TODO: Implement cloud API integration
        For now, returns stub response
        """
        logger.info("Querying cloud API")
        
        # TODO: Implement Gemini/OpenAI API call
        # Example:
        # import google.generativeai as genai
        # model = genai.GenerativeModel('gemini-1.5-flash')
        # response = model.generate_content(query)
        # return response.text
        
        # Stub response for now
        return f"[Cloud API Response] I received your query: '{query}'. Cloud API integration is ready for implementation."
    
    async def _query_stub(self, query: str) -> str:
        """
        Stub response when no models are available
        """
        return f"[Stub Response] Lyra AI received: '{query}'. Please configure a model to get intelligent responses."
    
    def get_recommended_mode(self) -> str:
        """
        Get recommended mode based on hardware
        """
        ram_gb = self.hardware_info["ram_gb"]
        has_gpu = self.hardware_info["has_gpu"]
        
        # High-end system
        if ram_gb >= 32 and has_gpu:
            return "offline-big"
        
        # Mid-range system
        elif ram_gb >= 16:
            return "hybrid"
        
        # Low-end system
        elif ram_gb >= 8:
            return "offline-mini"
        
        # Very low-end
        else:
            return "cloud"
