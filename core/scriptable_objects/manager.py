"""
Scriptable Object Manager
Manages templates and instances for a project
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from .template import ScriptableObjectTemplate
from .instance import ScriptableObjectInstance


class ScriptableObjectManager:
    """Manages scriptable object templates and instances for a project"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.templates_dir = self.project_path / "data" / "templates"
        self.instances_dir = self.project_path / "data" / "instances"
        
        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.instances_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, ScriptableObjectTemplate] = {}
        self.instances: Dict[str, Dict[str, ScriptableObjectInstance]] = {}  # template_name -> {instance_id -> instance}

        # Initialize subsystems (lazy import to avoid circular dependencies)
        self.undo_redo = None
        self.query_engine = None
        self.import_export = None

        self.load_all_templates()
        self.load_all_instances()
    
    # Template Management
    def create_template(self, name: str, description: str = "") -> ScriptableObjectTemplate:
        """Create a new template"""
        if name in self.templates:
            raise ValueError(f"Template '{name}' already exists")
        
        template = ScriptableObjectTemplate(name, description)
        self.templates[name] = template
        return template
    
    def save_template(self, template: ScriptableObjectTemplate):
        """Save a template to disk"""
        template_file = self.templates_dir / f"{template.name}.json"
        template.save_to_file(str(template_file))
        
        # Also generate Python file
        python_file = self.templates_dir / f"{template.name}.py"
        template.generate_python_file(str(python_file))
        
        self.templates[template.name] = template
    
    def load_template(self, name: str) -> Optional[ScriptableObjectTemplate]:
        """Load a template from disk"""
        template_file = self.templates_dir / f"{name}.json"
        if template_file.exists():
            template = ScriptableObjectTemplate.load_from_file(str(template_file))
            if template:
                self.templates[name] = template
            return template
        return None
    
    def load_all_templates(self):
        """Load all templates from disk"""
        self.templates.clear()
        
        if not self.templates_dir.exists():
            return
        
        for template_file in self.templates_dir.glob("*.json"):
            template = ScriptableObjectTemplate.load_from_file(str(template_file))
            if template:
                self.templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[ScriptableObjectTemplate]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def get_all_templates(self) -> List[ScriptableObjectTemplate]:
        """Get all templates"""
        return list(self.templates.values())
    
    def delete_template(self, name: str) -> bool:
        """Delete a template and all its instances"""
        if name not in self.templates:
            return False
        
        # Delete template files
        template_file = self.templates_dir / f"{name}.json"
        python_file = self.templates_dir / f"{name}.py"
        
        if template_file.exists():
            template_file.unlink()
        if python_file.exists():
            python_file.unlink()
        
        # Delete all instances of this template
        self.delete_all_instances_of_template(name)
        
        # Remove from memory
        del self.templates[name]
        return True
    
    # Instance Management
    def create_instance(self, template_name: str, instance_name: Optional[str] = None, **kwargs) -> Optional[ScriptableObjectInstance]:
        """Create a new instance of a template"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        # Create instance with default data from template
        default_data = template.create_default_instance_data()
        default_data.update(kwargs)
        
        instance = ScriptableObjectInstance(
            template_name=template_name,
            name=instance_name or f"{template_name}_instance",
            **default_data
        )
        
        # Add to instances
        if template_name not in self.instances:
            self.instances[template_name] = {}
        
        self.instances[template_name][instance.instance_id] = instance
        return instance
    
    def save_instance(self, instance: ScriptableObjectInstance):
        """Save an instance to disk"""
        template_instances_dir = self.instances_dir / instance.template_name
        template_instances_dir.mkdir(parents=True, exist_ok=True)
        
        instance_file = template_instances_dir / f"{instance.instance_id}.json"
        instance.save_to_file(str(instance_file))
        
        # Update in memory
        if instance.template_name not in self.instances:
            self.instances[instance.template_name] = {}
        self.instances[instance.template_name][instance.instance_id] = instance
    
    def load_all_instances(self):
        """Load all instances from disk"""
        self.instances.clear()
        
        if not self.instances_dir.exists():
            return
        
        for template_dir in self.instances_dir.iterdir():
            if template_dir.is_dir():
                template_name = template_dir.name
                self.instances[template_name] = {}
                
                for instance_file in template_dir.glob("*.json"):
                    instance = ScriptableObjectInstance.load_from_file(str(instance_file))
                    if instance:
                        self.instances[template_name][instance.instance_id] = instance
    
    def get_instance(self, template_name: str, instance_id: str) -> Optional[ScriptableObjectInstance]:
        """Get a specific instance"""
        return self.instances.get(template_name, {}).get(instance_id)
    
    def get_instances_of_template(self, template_name: str) -> List[ScriptableObjectInstance]:
        """Get all instances of a template"""
        return list(self.instances.get(template_name, {}).values())
    
    def get_all_instances(self) -> Dict[str, List[ScriptableObjectInstance]]:
        """Get all instances organized by template"""
        result = {}
        for template_name, instances in self.instances.items():
            result[template_name] = list(instances.values())
        return result
    
    def delete_instance(self, template_name: str, instance_id: str) -> bool:
        """Delete a specific instance"""
        if template_name not in self.instances or instance_id not in self.instances[template_name]:
            return False
        
        # Delete file
        instance_file = self.instances_dir / template_name / f"{instance_id}.json"
        if instance_file.exists():
            instance_file.unlink()
        
        # Remove from memory
        del self.instances[template_name][instance_id]
        
        # Clean up empty template directory
        if not self.instances[template_name]:
            del self.instances[template_name]
            template_dir = self.instances_dir / template_name
            if template_dir.exists() and not any(template_dir.iterdir()):
                template_dir.rmdir()
        
        return True
    
    def delete_all_instances_of_template(self, template_name: str):
        """Delete all instances of a template"""
        if template_name in self.instances:
            # Delete all instance files
            template_dir = self.instances_dir / template_name
            if template_dir.exists():
                for instance_file in template_dir.glob("*.json"):
                    instance_file.unlink()
                template_dir.rmdir()
            
            # Remove from memory
            del self.instances[template_name]
    
    def get_template_categories(self) -> List[str]:
        """Get all unique template categories"""
        categories = set()
        for template in self.templates.values():
            if template.category:
                categories.add(template.category)
        return sorted(list(categories))
    
    def get_templates_by_category(self, category: str) -> List[ScriptableObjectTemplate]:
        """Get templates in a specific category"""
        return [t for t in self.templates.values() if t.category == category]
    
    def validate_all_instances(self) -> Dict[str, List[str]]:
        """Validate all instances against their templates"""
        errors = {}
        
        for template_name, instances in self.instances.items():
            template = self.get_template(template_name)
            if not template:
                errors[template_name] = [f"Template '{template_name}' not found"]
                continue
            
            for instance_id, instance in instances.items():
                instance_errors = instance.validate_against_template(template)
                if instance_errors:
                    errors[f"{template_name}/{instance_id}"] = instance_errors
        
        return errors

    # Enhanced functionality methods

    def get_undo_redo_manager(self):
        """Get the undo/redo manager"""
        if self.undo_redo is None:
            from .undo_redo import UndoRedoManager
            self.undo_redo = UndoRedoManager()
        return self.undo_redo

    def get_query_engine(self):
        """Get the query engine"""
        if self.query_engine is None:
            from .query import QueryEngine
            self.query_engine = QueryEngine(self)
        return self.query_engine

    def get_import_export_manager(self):
        """Get the import/export manager"""
        if self.import_export is None:
            from .import_export import ImportExportManager
            self.import_export = ImportExportManager(self)
        return self.import_export

    def find_instances_by_query(self, template_name: str, query_builder):
        """Find instances using query builder"""
        return self.get_query_engine().execute(template_name, query_builder)

    def search_instances(self, template_name: str, search_text: str, fields: Optional[List[str]] = None):
        """Search instances by text"""
        return self.get_query_engine().search_text(template_name, search_text, fields)

    def get_template_hierarchy(self, template_name: str) -> List[str]:
        """Get the inheritance hierarchy for a template"""
        hierarchy = []
        current_template = self.get_template(template_name)

        while current_template:
            hierarchy.append(current_template.name)
            if current_template.parent_template:
                current_template = self.get_template(current_template.parent_template)
            else:
                break

        return hierarchy

    def get_derived_templates(self, template_name: str) -> List[ScriptableObjectTemplate]:
        """Get templates that inherit from the given template"""
        derived = []
        for template in self.templates.values():
            if template.parent_template == template_name:
                derived.append(template)
        return derived

    def validate_template_hierarchy(self) -> Dict[str, List[str]]:
        """Validate template inheritance hierarchy for circular dependencies"""
        errors = {}

        for template_name, template in self.templates.items():
            if template.parent_template:
                visited = set()
                current = template

                while current and current.parent_template:
                    if current.parent_template in visited:
                        errors[template_name] = [f"Circular inheritance detected: {' -> '.join(visited)} -> {current.parent_template}"]
                        break

                    visited.add(current.name)
                    current = self.get_template(current.parent_template)

                    if not current:
                        if template_name not in errors:
                            errors[template_name] = []
                        errors[template_name].append(f"Parent template '{template.parent_template}' not found")
                        break

        return errors
