"""
Scriptable Object Instance
Represents an instance of a scriptable object template with specific data
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path


class ScriptableObjectInstance:
    """Base class for scriptable object instances"""
    
    def __init__(self, template_name: str, instance_id: str = None, **kwargs):
        self.template_name = template_name
        self.instance_id = instance_id or str(uuid.uuid4())
        self.name = kwargs.get("name", f"{template_name}_{self.instance_id[:8]}")
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        
        # Set initial data from kwargs
        for key, value in kwargs.items():
            if key not in ["template_name", "instance_id", "name"]:
                self.data[key] = value
    
    def get_value(self, field_name: str, default: Any = None) -> Any:
        """Get a field value"""
        return self.data.get(field_name, default)
    
    def set_value(self, field_name: str, value: Any):
        """Set a field value"""
        self.data[field_name] = value
    
    def has_field(self, field_name: str) -> bool:
        """Check if instance has a field"""
        return field_name in self.data
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all instance data"""
        return self.data.copy()
    
    def update_data(self, new_data: Dict[str, Any]):
        """Update instance data"""
        self.data.update(new_data)
    
    def clear_data(self):
        """Clear all instance data"""
        self.data.clear()
    
    def clone(self, new_name: str = None) -> 'ScriptableObjectInstance':
        """Create a copy of this instance"""
        new_instance = ScriptableObjectInstance(
            template_name=self.template_name,
            name=new_name or f"{self.name}_copy",
            **self.data
        )
        new_instance.metadata = self.metadata.copy()
        return new_instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary for serialization"""
        return {
            "template_name": self.template_name,
            "instance_id": self.instance_id,
            "name": self.name,
            "data": self.data,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptableObjectInstance':
        """Create instance from dictionary"""
        instance = cls(
            template_name=data.get("template_name", ""),
            instance_id=data.get("instance_id"),
            name=data.get("name", "")
        )
        instance.data = data.get("data", {})
        instance.metadata = data.get("metadata", {})
        return instance
    
    def save_to_file(self, file_path: str):
        """Save instance to JSON file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['ScriptableObjectInstance']:
        """Load instance from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading instance from {file_path}: {e}")
            return None
    
    def validate_against_template(self, template) -> List[str]:
        """Validate this instance against its template"""
        if hasattr(template, 'validate_instance_data'):
            return template.validate_instance_data(self.data)
        return []
    
    def _ready(self):
        """Called when the object is ready - override in subclasses"""
        pass
    
    def _process(self, delta: float):
        """Called every frame - override in subclasses"""
        pass
    
    def _physics_process(self, delta: float):
        """Called every physics frame - override in subclasses"""
        pass
    
    def __getattr__(self, name: str) -> Any:
        """Allow direct access to data fields as attributes"""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any):
        """Allow direct setting of data fields as attributes"""
        # Handle special attributes normally
        if name in ["template_name", "instance_id", "name", "data", "metadata"]:
            super().__setattr__(name, value)
        else:
            # Store other attributes in data
            if hasattr(self, 'data'):
                self.data[name] = value
            else:
                super().__setattr__(name, value)
    
    def __repr__(self) -> str:
        return f"ScriptableObjectInstance(template='{self.template_name}', name='{self.name}', id='{self.instance_id}')"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.template_name})"
