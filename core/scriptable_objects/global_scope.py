"""
Global Scope System for Scriptable Objects
Provides dynamic access to scriptable objects through global namespace
with lazy loading and caching for performance
"""

import re
import weakref
from typing import Dict, Any, Optional, List, Set
from pathlib import Path
import threading
import time

from .manager import ScriptableObjectManager
from .instance import ScriptableObjectInstance
from .template import ScriptableObjectTemplate


class InstanceProxy:
    """Proxy object that represents a scriptable object instance in global scope"""
    
    def __init__(self, template_name: str, instance_name: str, instance_id: str, manager: 'GlobalScopeManager'):
        self._template_name = template_name
        self._instance_name = instance_name
        self._instance_id = instance_id
        self._manager = manager
        self._instance: Optional[ScriptableObjectInstance] = None
        self._last_accessed = time.time()
        self._lock = threading.RLock()
    
    def _load_instance(self) -> Optional[ScriptableObjectInstance]:
        """Load the actual instance if not already loaded"""
        with self._lock:
            if self._instance is None:
                self._instance = self._manager.loader.load_instance_by_id(self._template_name, self._instance_id)
                self._last_accessed = time.time()
            return self._instance
    
    def _unload_instance(self):
        """Unload the instance to free memory"""
        with self._lock:
            self._instance = None
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from the instance"""
        instance = self._load_instance()
        if instance is None:
            raise AttributeError(f"Instance {self._template_name}.{self._instance_name} not found")
        
        self._last_accessed = time.time()
        
        # First try to get from instance data
        if instance.has_field(name):
            return instance.get_value(name)
        
        # Then try to get methods or other attributes
        if hasattr(instance, name):
            attr = getattr(instance, name)
            # If it's a method, wrap it to update access time
            if callable(attr):
                def wrapped_method(*args, **kwargs):
                    self._last_accessed = time.time()
                    return attr(*args, **kwargs)
                return wrapped_method
            return attr
        
        raise AttributeError(f"'{self._template_name}.{self._instance_name}' has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any):
        """Set attribute on the instance"""
        if name.startswith('_'):
            # Internal attributes
            super().__setattr__(name, value)
            return
        
        instance = self._load_instance()
        if instance is None:
            raise AttributeError(f"Instance {self._template_name}.{self._instance_name} not found")
        
        self._last_accessed = time.time()
        instance.set_value(name, value)
    
    def __repr__(self) -> str:
        return f"<InstanceProxy: {self._template_name}.{self._instance_name}>"
    
    def __str__(self) -> str:
        return f"{self._template_name}.{self._instance_name}"


class TemplateProxy:
    """Proxy object that represents a template in global scope"""
    
    def __init__(self, template_name: str, manager: 'GlobalScopeManager'):
        self._template_name = template_name
        self._manager = manager
        self._instances: Dict[str, InstanceProxy] = {}
        self._loaded = False
        self._lock = threading.RLock()
    
    def _load_instances(self):
        """Load instance proxies for this template"""
        with self._lock:
            if self._loaded:
                return
            
            # Get all instances of this template
            instances = self._manager.loader.get_all_instances_of_template(self._template_name)
            
            for instance in instances:
                safe_name = self._manager._make_safe_name(instance.name)
                proxy = InstanceProxy(self._template_name, instance.name, instance.instance_id, self._manager)
                self._instances[safe_name] = proxy
            
            self._loaded = True
    
    def _get_instance_proxy(self, instance_name: str) -> Optional[InstanceProxy]:
        """Get an instance proxy by name"""
        self._load_instances()
        safe_name = self._manager._make_safe_name(instance_name)
        return self._instances.get(safe_name)
    
    def __getattr__(self, name: str) -> InstanceProxy:
        """Get an instance by name"""
        if name.startswith('_'):
            raise AttributeError(f"'{self._template_name}' has no attribute '{name}'")
        
        proxy = self._get_instance_proxy(name)
        if proxy is None:
            # Try to find by original name (in case of name conversion issues)
            self._load_instances()
            for safe_name, instance_proxy in self._instances.items():
                if safe_name == name or instance_proxy._instance_name == name:
                    return instance_proxy
            
            raise AttributeError(f"Template '{self._template_name}' has no instance '{name}'")
        
        return proxy
    
    def __dir__(self) -> List[str]:
        """Return list of available instances"""
        self._load_instances()
        return list(self._instances.keys())
    
    def __repr__(self) -> str:
        return f"<TemplateProxy: {self._template_name}>"
    
    def __str__(self) -> str:
        return self._template_name


class GlobalScopeManager:
    """Manages the global scope for scriptable objects"""
    
    def __init__(self, loader: 'ScriptableObjectLoader', cache_size: int = 100, cache_timeout: float = 300.0):
        self.loader = loader
        self.cache_size = cache_size
        self.cache_timeout = cache_timeout
        
        self._templates: Dict[str, TemplateProxy] = {}
        self._instance_cache: Dict[str, InstanceProxy] = {}
        self._cache_access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # Start cache cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cache_cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _make_safe_name(self, name: str) -> str:
        """Convert a name to a safe Python identifier"""
        # Replace spaces and special characters with underscores
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Ensure it starts with a letter or underscore
        if safe_name and safe_name[0].isdigit():
            safe_name = '_' + safe_name
        
        # Remove multiple consecutive underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Remove trailing underscores
        safe_name = safe_name.rstrip('_')
        
        return safe_name or '_unnamed'
    
    def _cache_cleanup_loop(self):
        """Background thread to clean up old cache entries"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                self._cleanup_cache()
            except Exception as e:
                print(f"Error in cache cleanup: {e}")
    
    def _cleanup_cache(self):
        """Remove old entries from cache"""
        with self._lock:
            current_time = time.time()
            to_remove = []
            
            # Find expired entries
            for key, proxy in self._instance_cache.items():
                if hasattr(proxy, '_last_accessed'):
                    if current_time - proxy._last_accessed > self.cache_timeout:
                        to_remove.append(key)
            
            # Remove expired entries
            for key in to_remove:
                if key in self._instance_cache:
                    proxy = self._instance_cache[key]
                    if hasattr(proxy, '_unload_instance'):
                        proxy._unload_instance()
                    del self._instance_cache[key]
                    if key in self._cache_access_times:
                        del self._cache_access_times[key]
            
            # If still over cache size, remove least recently used
            if len(self._instance_cache) > self.cache_size:
                # Sort by access time
                sorted_items = sorted(
                    self._instance_cache.items(),
                    key=lambda x: getattr(x[1], '_last_accessed', 0)
                )
                
                # Remove oldest entries
                excess_count = len(self._instance_cache) - self.cache_size
                for i in range(excess_count):
                    key, proxy = sorted_items[i]
                    if hasattr(proxy, '_unload_instance'):
                        proxy._unload_instance()
                    del self._instance_cache[key]
                    if key in self._cache_access_times:
                        del self._cache_access_times[key]
    
    def get_template_proxy(self, template_name: str) -> Optional[TemplateProxy]:
        """Get a template proxy by name"""
        safe_name = self._make_safe_name(template_name)
        
        if safe_name not in self._templates:
            # Check if template exists
            template = self.loader.get_template(template_name)
            if template is None:
                return None
            
            self._templates[safe_name] = TemplateProxy(template_name, self)
        
        return self._templates[safe_name]
    
    def refresh_templates(self):
        """Refresh the template list"""
        with self._lock:
            self._templates.clear()
            self._instance_cache.clear()
            self._cache_access_times.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "template_proxies": len(self._templates),
                "cached_instances": len(self._instance_cache),
                "cache_size_limit": self.cache_size,
                "cache_timeout": self.cache_timeout
            }
    
    def clear_cache(self):
        """Clear all cached instances"""
        with self._lock:
            for proxy in self._instance_cache.values():
                if hasattr(proxy, '_unload_instance'):
                    proxy._unload_instance()
            self._instance_cache.clear()
            self._cache_access_times.clear()


class GlobalScopeNamespace:
    """Main namespace object that provides access to all templates"""
    
    def __init__(self, manager: GlobalScopeManager):
        self._manager = manager
    
    def __getattr__(self, name: str) -> TemplateProxy:
        """Get a template by name"""
        if name.startswith('_'):
            raise AttributeError(f"No attribute '{name}'")
        
        # Try to find template by safe name
        templates = self._manager.loader.get_all_templates()
        
        for template in templates:
            safe_name = self._manager._make_safe_name(template.name)
            if safe_name == name:
                proxy = self._manager.get_template_proxy(template.name)
                if proxy:
                    return proxy
        
        # Try to find by original name
        for template in templates:
            if template.name == name:
                proxy = self._manager.get_template_proxy(template.name)
                if proxy:
                    return proxy
        
        raise AttributeError(f"No template found with name '{name}'")
    
    def __dir__(self) -> List[str]:
        """Return list of available templates"""
        templates = self._manager.loader.get_all_templates()
        return [self._manager._make_safe_name(template.name) for template in templates]
    
    def __repr__(self) -> str:
        return "<ScriptableObjectsNamespace>"


# Global instance
_global_scope_manager: Optional[GlobalScopeManager] = None
_global_namespace: Optional[GlobalScopeNamespace] = None


def initialize_global_scope(loader, cache_size: int = 100, cache_timeout: float = 300.0):
    """Initialize the global scope system"""
    global _global_scope_manager, _global_namespace
    
    _global_scope_manager = GlobalScopeManager(loader, cache_size, cache_timeout)
    _global_namespace = GlobalScopeNamespace(_global_scope_manager)


def get_global_namespace() -> Optional[GlobalScopeNamespace]:
    """Get the global namespace object"""
    return _global_namespace


def get_global_scope_manager() -> Optional[GlobalScopeManager]:
    """Get the global scope manager"""
    return _global_scope_manager


def refresh_global_scope():
    """Refresh the global scope (reload templates)"""
    if _global_scope_manager:
        _global_scope_manager.refresh_templates()


def clear_global_cache():
    """Clear the global cache"""
    if _global_scope_manager:
        _global_scope_manager.clear_cache()


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics"""
    if _global_scope_manager:
        return _global_scope_manager.get_cache_stats()
    return {}


# Convenience function to inject into global namespace
def inject_into_globals(globals_dict: Dict[str, Any], prefix: str = "SO"):
    """Inject the scriptable objects namespace into a global dictionary"""
    if _global_namespace:
        globals_dict[prefix] = _global_namespace
