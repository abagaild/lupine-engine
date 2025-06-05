"""
Scriptable Object Runtime Loader
Provides runtime loading and caching of scriptable object instances
"""

import os
import json
from typing import Dict, Optional, Any, List
from pathlib import Path

from .instance import ScriptableObjectInstance
from .template import ScriptableObjectTemplate


class ScriptableObjectLoader:
    """Runtime loader for scriptable objects with caching"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.templates_dir = self.project_path / "data" / "templates"
        self.instances_dir = self.project_path / "data" / "instances"
        
        # Caches
        self.template_cache: Dict[str, ScriptableObjectTemplate] = {}
        self.instance_cache: Dict[str, ScriptableObjectInstance] = {}
        self.instance_lookup: Dict[str, str] = {}  # name -> instance_id
        
        # Load all templates at startup
        self._load_all_templates()
        self._build_instance_lookup()
    
    def _load_all_templates(self):
        """Load all templates into cache"""
        if not self.templates_dir.exists():
            return
        
        for template_file in self.templates_dir.glob("*.json"):
            template = ScriptableObjectTemplate.load_from_file(str(template_file))
            if template:
                self.template_cache[template.name] = template
    
    def _build_instance_lookup(self):
        """Build lookup table for instance names to IDs"""
        if not self.instances_dir.exists():
            return
        
        for template_dir in self.instances_dir.iterdir():
            if template_dir.is_dir():
                for instance_file in template_dir.glob("*.json"):
                    try:
                        with open(instance_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        instance_id = data.get("instance_id")
                        name = data.get("name")
                        
                        if instance_id and name:
                            self.instance_lookup[name] = instance_id
                    except Exception as e:
                        print(f"Error reading instance file {instance_file}: {e}")
    
    def get_template(self, template_name: str) -> Optional[ScriptableObjectTemplate]:
        """Get a template by name"""
        return self.template_cache.get(template_name)

    def get_all_templates(self) -> List[ScriptableObjectTemplate]:
        """Get all templates"""
        return list(self.template_cache.values())
    
    def load_instance_by_id(self, template_name: str, instance_id: str) -> Optional[ScriptableObjectInstance]:
        """Load an instance by template name and instance ID"""
        cache_key = f"{template_name}:{instance_id}"
        
        # Check cache first
        if cache_key in self.instance_cache:
            return self.instance_cache[cache_key]
        
        # Load from disk
        instance_file = self.instances_dir / template_name / f"{instance_id}.json"
        if not instance_file.exists():
            return None
        
        instance = ScriptableObjectInstance.load_from_file(str(instance_file))
        if instance:
            self.instance_cache[cache_key] = instance
        
        return instance
    
    def load_instance_by_name(self, name: str) -> Optional[ScriptableObjectInstance]:
        """Load an instance by name (searches all templates)"""
        # Search through all instances to find by name
        for template_name in self.template_cache.keys():
            template_dir = self.instances_dir / template_name
            if not template_dir.exists():
                continue

            for instance_file in template_dir.glob("*.json"):
                try:
                    with open(instance_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if data.get("name") == name:
                        instance_id = data.get("instance_id")
                        if instance_id:
                            return self.load_instance_by_id(template_name, instance_id)
                except Exception:
                    continue

        return None
    
    def load_instance(self, template_name: str, identifier: str) -> Optional[ScriptableObjectInstance]:
        """Load an instance by template name and either name or ID"""
        # Try as instance ID first
        instance = self.load_instance_by_id(template_name, identifier)
        if instance:
            return instance
        
        # Try as name
        return self.load_instance_by_name(identifier)
    
    def get_all_instances_of_template(self, template_name: str) -> List[ScriptableObjectInstance]:
        """Get all instances of a specific template"""
        instances = []
        template_dir = self.instances_dir / template_name
        
        if not template_dir.exists():
            return instances
        
        for instance_file in template_dir.glob("*.json"):
            instance_id = instance_file.stem
            instance = self.load_instance_by_id(template_name, instance_id)
            if instance:
                instances.append(instance)
        
        return instances
    
    def find_instances_by_field(self, template_name: str, field_name: str, value: Any) -> List[ScriptableObjectInstance]:
        """Find instances where a field matches a specific value"""
        matching_instances = []
        
        for instance in self.get_all_instances_of_template(template_name):
            if instance.get_value(field_name) == value:
                matching_instances.append(instance)
        
        return matching_instances
    
    def find_instances_by_criteria(self, template_name: str, criteria: Dict[str, Any]) -> List[ScriptableObjectInstance]:
        """Find instances matching multiple field criteria"""
        matching_instances = []
        
        for instance in self.get_all_instances_of_template(template_name):
            matches = True
            for field_name, expected_value in criteria.items():
                if instance.get_value(field_name) != expected_value:
                    matches = False
                    break
            
            if matches:
                matching_instances.append(instance)
        
        return matching_instances
    
    def preload_template_instances(self, template_name: str):
        """Preload all instances of a template into cache"""
        self.get_all_instances_of_template(template_name)
    
    def clear_cache(self):
        """Clear the instance cache (templates remain loaded)"""
        self.instance_cache.clear()
    
    def reload_templates(self):
        """Reload all templates from disk"""
        self.template_cache.clear()
        self._load_all_templates()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "templates_loaded": len(self.template_cache),
            "instances_cached": len(self.instance_cache),
            "names_indexed": len(self.instance_lookup)
        }


# Global loader instance (initialized when needed)
_global_loader: Optional[ScriptableObjectLoader] = None


def initialize_loader(project_path: str, enable_global_scope: bool = True, cache_size: int = 100, cache_timeout: float = 300.0):
    """Initialize the global scriptable object loader"""
    global _global_loader
    _global_loader = ScriptableObjectLoader(project_path)

    # Initialize global scope if requested
    if enable_global_scope:
        from .global_scope import initialize_global_scope
        initialize_global_scope(_global_loader, cache_size, cache_timeout)


def get_loader() -> Optional[ScriptableObjectLoader]:
    """Get the global loader instance"""
    return _global_loader


def load_scriptable_object(template_name: str, identifier: str) -> Optional[ScriptableObjectInstance]:
    """Convenience function to load a scriptable object"""
    if _global_loader:
        return _global_loader.load_instance(template_name, identifier)
    return None


def find_scriptable_objects(template_name: str, **criteria) -> List[ScriptableObjectInstance]:
    """Convenience function to find scriptable objects by criteria"""
    if _global_loader:
        return _global_loader.find_instances_by_criteria(template_name, criteria)
    return []


# Example usage functions for game scripts
def load_item(item_name: str) -> Optional[ScriptableObjectInstance]:
    """Load an item by name"""
    return load_scriptable_object("Item", item_name)


def load_character(character_name: str) -> Optional[ScriptableObjectInstance]:
    """Load a character by name"""
    return load_scriptable_object("Character", character_name)


def load_quest(quest_name: str) -> Optional[ScriptableObjectInstance]:
    """Load a quest by name"""
    return load_scriptable_object("Quest", quest_name)


def find_items_by_type(item_type: str) -> List[ScriptableObjectInstance]:
    """Find all items of a specific type"""
    return find_scriptable_objects("Item", item_type=item_type)


def find_characters_in_area(area_name: str) -> List[ScriptableObjectInstance]:
    """Find all characters in a specific area"""
    return find_scriptable_objects("Character", area=area_name)


def find_available_quests(player_level: int) -> List[ScriptableObjectInstance]:
    """Find quests available to a player of specific level"""
    if not _global_loader:
        return []

    available_quests = []
    for quest in _global_loader.get_all_instances_of_template("Quest"):
        required_level = quest.get_value("required_level", 1)
        if required_level <= player_level:
            available_quests.append(quest)

    return available_quests


# Global scope access functions

def get_scriptable_objects():
    """Get the global scriptable objects namespace"""
    from .global_scope import get_global_namespace
    return get_global_namespace()


def inject_scriptable_objects(globals_dict: Dict[str, Any], name: str = "SO"):
    """Inject scriptable objects into a global namespace"""
    from .global_scope import inject_into_globals
    inject_into_globals(globals_dict, name)


def refresh_scriptable_objects():
    """Refresh the global scriptable objects cache"""
    from .global_scope import refresh_global_scope
    refresh_global_scope()


def clear_scriptable_objects_cache():
    """Clear the scriptable objects cache"""
    from .global_scope import clear_global_cache
    clear_global_cache()


def get_scriptable_objects_stats():
    """Get scriptable objects cache statistics"""
    from .global_scope import get_cache_stats
    return get_cache_stats()
