"""
Dependency Injection Container
Manages singleton instances of all managers and services
"""

from typing import Dict, Type, TypeVar, Optional, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """
    Dependency Injection Container for managing service instances
    
    Features:
    - Singleton management
    - Lazy loading
    - Dependency resolution
    - Easy testing (mock dependencies)
    """
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register(self, service_type: Type[T], factory: Optional[callable] = None, singleton: bool = True) -> None:
        """
        Register a service type with optional factory function
        
        Args:
            service_type: The class type to register
            factory: Optional factory function to create instances
            singleton: If True, only one instance will be created
        """
        if factory:
            self._factories[service_type] = factory
        
        if singleton:
            self._singletons[service_type] = None
        
        logger.debug(f"Registered service: {service_type.__name__}")
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register a pre-created instance
        
        Args:
            service_type: The class type
            instance: The instance to register
        """
        self._services[service_type] = instance
        logger.debug(f"Registered instance: {service_type.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """
        Get an instance of the requested service
        
        Args:
            service_type: The class type to retrieve
            
        Returns:
            Instance of the requested service
        """
        # Check if instance already exists
        if service_type in self._services:
            return self._services[service_type]
        
        # Check if it's a singleton that's already been created
        if service_type in self._singletons and self._singletons[service_type] is not None:
            return self._singletons[service_type]
        
        # Create new instance
        instance = self._create_instance(service_type)
        
        # Store singleton
        if service_type in self._singletons:
            self._singletons[service_type] = instance
        
        # Store in services
        self._services[service_type] = instance
        
        return instance
    
    def _create_instance(self, service_type: Type[T]) -> T:
        """Create a new instance of the service"""
        if service_type in self._factories:
            # Use factory function
            factory = self._factories[service_type]
            instance = factory(self)
            logger.debug(f"Created instance via factory: {service_type.__name__}")
        else:
            # Try to instantiate directly
            try:
                instance = service_type()
                logger.debug(f"Created instance: {service_type.__name__}")
            except Exception as e:
                logger.error(f"Failed to create instance of {service_type.__name__}: {e}")
                raise
        
        return instance
    
    def has(self, service_type: Type) -> bool:
        """Check if a service is registered"""
        return service_type in self._services or service_type in self._factories or service_type in self._singletons
    
    def clear(self) -> None:
        """Clear all registered services (useful for testing)"""
        self._services.clear()
        self._singletons.clear()
        logger.debug("Container cleared")
    
    def reset_singleton(self, service_type: Type) -> None:
        """Reset a singleton instance (will be recreated on next get())"""
        if service_type in self._singletons:
            self._singletons[service_type] = None
        if service_type in self._services:
            del self._services[service_type]
        logger.debug(f"Reset singleton: {service_type.__name__}")


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)"""
    global _container
    _container = None


def initialize_core_services(config_dir: Optional[Any] = None) -> ServiceContainer:
    """
    Initialize and register all core services
    
    Args:
        config_dir: Path to configuration directory
        
    Returns:
        Configured ServiceContainer
    """
    from pathlib import Path
    from core.managers.config_manager import ConfigManager
    from core.managers.permission_manager import PermissionManager
    from core.managers.model_registry import ModelRegistry
    from error.error_handler import ErrorHandler, get_error_handler
    from core.memory_watchdog import MemoryWatchdog
    
    container = get_container()
    
    # 1. Error Handler (Foundation)
    # Usually initialized early, but we register it here to be safe
    error_handler = get_error_handler()
    container.register_instance(ErrorHandler, error_handler)
    
    # 2. Config Manager (Foundation)
    if config_dir is None:
        # Default to relative path if not provided
        config_dir = Path(__file__).parent.parent.parent / "config"
    
    config_manager = ConfigManager(Path(config_dir))
    container.register_instance(ConfigManager, config_manager)
    
    # 3. Permission Manager (Depends on Config + Error)
    def create_permission_manager(c: ServiceContainer):
        return PermissionManager(
            c.get(ConfigManager),
            c.get(ErrorHandler)
        )
    container.register(PermissionManager, factory=create_permission_manager)
    
    # 4. Model Registry (Depends on Config + Error)
    def create_model_registry(c: ServiceContainer):
        return ModelRegistry(
            c.get(ConfigManager),
            c.get(ErrorHandler)
        )
    container.register(ModelRegistry, factory=create_model_registry)
    
    # 5. Memory Watchdog (Depends on Config)
    def create_memory_watchdog(c: ServiceContainer):
        return MemoryWatchdog.from_config(c.get(ConfigManager))
    container.register(MemoryWatchdog, factory=create_memory_watchdog)
    
    logger.info("Core services initialized and registered")
    return container
