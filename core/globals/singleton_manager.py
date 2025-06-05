"""
Singleton Manager for Lupine Engine
Manages global singleton scripts similar to Godot's autoload system
"""

import json
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import threading


class SingletonDefinition:
    """Represents a singleton script definition"""
    
    def __init__(self, name: str, script_path: str, enabled: bool = True):
        self.name = name
        self.script_path = script_path
        self.enabled = enabled
        self.instance: Optional[Any] = None
        self._module = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "script_path": self.script_path,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SingletonDefinition':
        """Create from dictionary"""
        return cls(
            name=data["name"],
            script_path=data["script_path"],
            enabled=data.get("enabled", True)
        )


class SingletonManager:
    """Manages global singleton instances"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.singletons: Dict[str, SingletonDefinition] = {}
        self.instances: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._initialized = False
        
        # Load existing singletons
        self.load_singletons()
    
    def add_singleton(self, name: str, script_path: str, enabled: bool = True) -> bool:
        """Add a new singleton definition"""
        with self._lock:
            if name in self.singletons:
                return False
            
            # Validate script path
            full_path = self.project_path / script_path
            if not full_path.exists():
                return False
            
            singleton = SingletonDefinition(name, script_path, enabled)
            self.singletons[name] = singleton
            
            # Initialize if enabled and manager is initialized
            if enabled and self._initialized:
                self._initialize_singleton(singleton)
            
            return True
    
    def remove_singleton(self, name: str) -> bool:
        """Remove a singleton definition"""
        with self._lock:
            if name not in self.singletons:
                return False
            
            # Clean up instance
            if name in self.instances:
                instance = self.instances[name]
                if hasattr(instance, '_singleton_cleanup'):
                    try:
                        instance._singleton_cleanup()
                    except Exception as e:
                        print(f"Error during singleton cleanup for {name}: {e}")
                del self.instances[name]
            
            del self.singletons[name]
            return True
    
    def update_singleton(self, name: str, script_path: Optional[str] = None, enabled: Optional[bool] = None) -> bool:
        """Update singleton definition"""
        with self._lock:
            if name not in self.singletons:
                return False
            
            singleton = self.singletons[name]
            old_enabled = singleton.enabled
            
            if script_path is not None:
                # Validate new script path
                full_path = self.project_path / script_path
                if not full_path.exists():
                    return False
                singleton.script_path = script_path
            
            if enabled is not None:
                singleton.enabled = enabled
            
            # Handle state changes
            if self._initialized:
                if old_enabled and not singleton.enabled:
                    # Disable singleton
                    if name in self.instances:
                        instance = self.instances[name]
                        if hasattr(instance, '_singleton_cleanup'):
                            try:
                                instance._singleton_cleanup()
                            except Exception as e:
                                print(f"Error during singleton cleanup for {name}: {e}")
                        del self.instances[name]
                
                elif not old_enabled and singleton.enabled:
                    # Enable singleton
                    self._initialize_singleton(singleton)
                
                elif singleton.enabled and script_path is not None:
                    # Reload singleton with new script
                    if name in self.instances:
                        instance = self.instances[name]
                        if hasattr(instance, '_singleton_cleanup'):
                            try:
                                instance._singleton_cleanup()
                            except Exception as e:
                                print(f"Error during singleton cleanup for {name}: {e}")
                        del self.instances[name]
                    self._initialize_singleton(singleton)
            
            return True
    
    def get_singleton(self, name: str) -> Optional[Any]:
        """Get singleton instance by name"""
        with self._lock:
            return self.instances.get(name)
    
    def get_all_singletons(self) -> List[SingletonDefinition]:
        """Get all singleton definitions"""
        with self._lock:
            return list(self.singletons.values())
    
    def initialize_all(self):
        """Initialize all enabled singletons"""
        with self._lock:
            if self._initialized:
                return
            
            # Sort by name for consistent initialization order
            sorted_singletons = sorted(self.singletons.values(), key=lambda s: s.name)
            
            for singleton in sorted_singletons:
                if singleton.enabled:
                    self._initialize_singleton(singleton)
            
            self._initialized = True
    
    def _initialize_singleton(self, singleton: SingletonDefinition) -> bool:
        """Initialize a single singleton instance"""
        try:
            script_path = self.project_path / singleton.script_path
            
            # Load the module
            spec = importlib.util.spec_from_file_location(singleton.name, script_path)
            if spec is None or spec.loader is None:
                print(f"Failed to load singleton {singleton.name}: Invalid script")
                return False
            
            module = importlib.util.module_from_spec(spec)
            singleton._module = module
            
            # Execute the module
            spec.loader.exec_module(module)
            
            # Look for a main class or create instance
            instance = None
            
            # Try to find a class with the same name as the singleton
            if hasattr(module, singleton.name):
                cls = getattr(module, singleton.name)
                if isinstance(cls, type):
                    instance = cls()
            
            # Try to find a class named 'Singleton' or 'Main'
            if instance is None:
                for class_name in ['Singleton', 'Main', 'Global']:
                    if hasattr(module, class_name):
                        cls = getattr(module, class_name)
                        if isinstance(cls, type):
                            instance = cls()
                            break
            
            # If no class found, use the module itself
            if instance is None:
                instance = module
            
            # Call initialization method if it exists
            if hasattr(instance, '_singleton_init'):
                instance._singleton_init()
            
            self.instances[singleton.name] = instance
            singleton.instance = instance
            
            print(f"Initialized singleton: {singleton.name}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize singleton {singleton.name}: {e}")
            return False
    
    def save_singletons(self):
        """Save singleton definitions to project file"""
        try:
            config_file = self.project_path / "project.json"
            
            # Load existing project config
            config = {}
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
            
            # Update singletons section
            if "globals" not in config:
                config["globals"] = {}
            
            config["globals"]["singletons"] = [
                singleton.to_dict() for singleton in self.singletons.values()
            ]
            
            # Save back to file
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to save singletons: {e}")
            return False
    
    def load_singletons(self):
        """Load singleton definitions from project file"""
        try:
            config_file = self.project_path / "project.json"
            if not config_file.exists():
                return
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            singletons_data = config.get("globals", {}).get("singletons", [])
            
            for singleton_data in singletons_data:
                singleton = SingletonDefinition.from_dict(singleton_data)
                self.singletons[singleton.name] = singleton
            
        except Exception as e:
            print(f"Failed to load singletons: {e}")


# Global singleton manager instance
_singleton_manager: Optional[SingletonManager] = None


def get_singleton_manager() -> Optional[SingletonManager]:
    """Get the global singleton manager instance"""
    return _singleton_manager


def initialize_singleton_manager(project_path: str) -> SingletonManager:
    """Initialize the global singleton manager"""
    global _singleton_manager
    _singleton_manager = SingletonManager(project_path)
    return _singleton_manager


def get_singleton(name: str) -> Optional[Any]:
    """Get a singleton instance by name (convenience function)"""
    if _singleton_manager:
        return _singleton_manager.get_singleton(name)
    return None
