"""
Lazy Loader - Load Models Only When Needed
Prevents startup delays and memory waste
"""

import logging
import importlib
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class LazyModule:
    """
    Lazy-loaded module wrapper
    Imports module only when first accessed
    """
    
    def __init__(self, module_name: str):
        """
        Initialize lazy module
        
        Args:
            module_name: Name of module to lazy-load
        """
        self.module_name = module_name
        self._module: Optional[Any] = None
        self._loaded = False
        self._load_time: Optional[datetime] = None
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from module, loading if necessary"""
        if not self._loaded:
            self._load()
        return getattr(self._module, name)
    
    def _load(self):
        """Load the module"""
        if self._loaded:
            return
        
        logger.info(f"Lazy loading module: {self.module_name}")
        try:
            self._module = importlib.import_module(self.module_name)
            self._loaded = True
            self._load_time = datetime.now()
            logger.info(f"Module loaded: {self.module_name}")
        except Exception as e:
            logger.error(f"Failed to load module {self.module_name}: {e}")
            raise
    
    @property
    def is_loaded(self) -> bool:
        """Check if module is loaded"""
        return self._loaded
    
    def unload(self):
        """Unload the module"""
        if self._loaded:
            self._module = None
            self._loaded = False
            self._load_time = None
            logger.info(f"Module unloaded: {self.module_name}")


class LazyModelLoader:
    """
    Manages lazy loading of AI models
    Automatically unloads unused models after timeout
    """
    
    def __init__(self, auto_unload_timeout: int = 300):
        """
        Initialize lazy model loader
        
        Args:
            auto_unload_timeout: Seconds before unloading unused model
        """
        self.auto_unload_timeout = auto_unload_timeout
        self._models: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        
        logger.info(
            f"LazyModelLoader initialized: "
            f"auto_unload_timeout={auto_unload_timeout}s"
        )
    
    def register_model(
        self,
        model_name: str,
        loader_func: Callable[[], Any],
        unloader_func: Optional[Callable[[Any], None]] = None
    ):
        """
        Register a model for lazy loading
        
        Args:
            model_name: Unique name for the model
            loader_func: Function to load the model
            unloader_func: Optional function to unload the model
        """
        with self._lock:
            self._models[model_name] = {
                "loader": loader_func,
                "unloader": unloader_func,
                "instance": None,
                "loaded": False,
                "last_used": None
            }
        logger.info(f"Registered model: {model_name}")
    
    def get_model(self, model_name: str) -> Any:
        """
        Get model, loading if necessary
        
        Args:
            model_name: Name of model
        
        Returns:
            Model instance
        
        Raises:
            KeyError: If model not registered
        """
        if model_name not in self._models:
            raise KeyError(f"Model not registered: {model_name}")
        
        with self._lock:
            model_info = self._models[model_name]
            
            # Load if not loaded
            if not model_info["loaded"]:
                logger.info(f"Loading model: {model_name}")
                try:
                    model_info["instance"] = model_info["loader"]()
                    model_info["loaded"] = True
                    logger.info(f"Model loaded: {model_name}")
                except Exception as e:
                    logger.error(f"Failed to load model {model_name}: {e}")
                    raise
            
            # Update last used time
            model_info["last_used"] = datetime.now()
            
            return model_info["instance"]
    
    def unload_model(self, model_name: str):
        """
        Manually unload a model
        
        Args:
            model_name: Name of model
        """
        if model_name not in self._models:
            return
        
        with self._lock:
            model_info = self._models[model_name]
            
            if model_info["loaded"]:
                logger.info(f"Unloading model: {model_name}")
                
                # Call unloader if provided
                if model_info["unloader"]:
                    try:
                        model_info["unloader"](model_info["instance"])
                    except Exception as e:
                        logger.error(f"Error in unloader for {model_name}: {e}")
                
                # Clear instance
                model_info["instance"] = None
                model_info["loaded"] = False
                model_info["last_used"] = None
                
                # Force garbage collection
                import gc
                gc.collect()
                
                logger.info(f"Model unloaded: {model_name}")
    
    def start_auto_unload(self):
        """Start automatic unloading of unused models"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="ModelCleanup"
        )
        self._cleanup_thread.start()
        logger.info("Auto-unload started")
    
    def stop_auto_unload(self):
        """Stop automatic unloading"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2.0)
        logger.info("Auto-unload stopped")
    
    def _cleanup_loop(self):
        """Cleanup loop for auto-unloading"""
        import time
        
        while self._running:
            try:
                now = datetime.now()
                timeout_delta = timedelta(seconds=self.auto_unload_timeout)
                
                with self._lock:
                    for model_name, model_info in list(self._models.items()):
                        if not model_info["loaded"]:
                            continue
                        
                        last_used = model_info["last_used"]
                        if last_used and (now - last_used) > timeout_delta:
                            logger.info(
                                f"Auto-unloading {model_name} "
                                f"(unused for {self.auto_unload_timeout}s)"
                            )
                            self.unload_model(model_name)
                
                time.sleep(60)  # Check every minute
            
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                time.sleep(60)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all models
        
        Returns:
            Dictionary with model statuses
        """
        with self._lock:
            return {
                name: {
                    "loaded": info["loaded"],
                    "last_used": info["last_used"].isoformat() if info["last_used"] else None
                }
                for name, info in self._models.items()
            }


# Global lazy loader instance
_global_loader: Optional[LazyModelLoader] = None


def get_lazy_loader() -> LazyModelLoader:
    """Get global lazy loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = LazyModelLoader()
    return _global_loader


if __name__ == "__main__":
    # Test lazy loader
    import time
    
    print("Testing Lazy Loader")
    print("=" * 50)
    
    # Test lazy module
    print("\n1. Testing LazyModule:")
    lazy_json = LazyModule("json")
    print(f"Module loaded: {lazy_json.is_loaded}")
    data = lazy_json.dumps({"test": "data"})
    print(f"Module loaded: {lazy_json.is_loaded}")
    print(f"Result: {data}")
    
    # Test lazy model loader
    print("\n2. Testing LazyModelLoader:")
    
    def load_dummy_model():
        print("Loading dummy model...")
        time.sleep(1)
        return {"model": "dummy", "loaded": True}
    
    def unload_dummy_model(model):
        print(f"Unloading model: {model}")
    
    loader = LazyModelLoader(auto_unload_timeout=5)
    loader.register_model("dummy", load_dummy_model, unload_dummy_model)
    
    print("Getting model (should load)...")
    model = loader.get_model("dummy")
    print(f"Model: {model}")
    
    print("\nGetting model again (should not reload)...")
    model2 = loader.get_model("dummy")
    print(f"Same instance: {model is model2}")
    
    print("\nStatus:")
    print(loader.get_status())
    
    print("\nManual unload:")
    loader.unload_model("dummy")
    print(loader.get_status())
    
    print("=" * 50)
