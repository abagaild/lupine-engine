"""
Scriptable Object Template
Defines the structure and behavior of scriptable object types
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from .field import ScriptableObjectField, FieldType


class ScriptableObjectTemplate:
    """Represents a template for creating scriptable object instances"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.fields: List[ScriptableObjectField] = []
        self.base_code = ""  # Base code for the template
        self.icon_path = ""  # Optional icon for the template
        self.category = ""  # Category for organization
        self.version = "1.0.0"
        self.metadata: Dict[str, Any] = {}

        # Template inheritance
        self.parent_template: Optional[str] = None  # Name of parent template
        self.is_abstract: bool = False  # Whether this template can be instantiated

        # Validation rules
        self.validation_rules: List[Dict[str, Any]] = []
    
    def add_field(self, field: ScriptableObjectField):
        """Add a field to the template"""
        # Check for duplicate names
        if any(f.name == field.name for f in self.fields):
            raise ValueError(f"Field with name '{field.name}' already exists")
        
        self.fields.append(field)
    
    def remove_field(self, field_name: str) -> bool:
        """Remove a field by name"""
        for i, field in enumerate(self.fields):
            if field.name == field_name:
                del self.fields[i]
                return True
        return False
    
    def get_field(self, field_name: str) -> Optional[ScriptableObjectField]:
        """Get a field by name"""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def reorder_fields(self, field_names: List[str]):
        """Reorder fields according to the provided list"""
        new_fields = []
        for i, name in enumerate(field_names):
            field = self.get_field(name)
            if field:
                field.order = i
                new_fields.append(field)

        # Add any fields not in the list
        for field in self.fields:
            if field.name not in field_names:
                field.order = len(new_fields)
                new_fields.append(field)

        self.fields = new_fields

    def get_all_fields(self, manager=None) -> List[ScriptableObjectField]:
        """Get all fields including inherited ones"""
        all_fields = []

        # Get parent fields first
        if self.parent_template and manager:
            parent = manager.get_template(self.parent_template)
            if parent:
                all_fields.extend(parent.get_all_fields(manager))

        # Add own fields
        all_fields.extend(self.fields)

        # Sort by order
        all_fields.sort(key=lambda f: f.order)

        return all_fields

    def inherits_from(self, template_name: str, manager=None) -> bool:
        """Check if this template inherits from another template"""
        if not self.parent_template:
            return False

        if self.parent_template == template_name:
            return True

        if manager:
            parent = manager.get_template(self.parent_template)
            if parent:
                return parent.inherits_from(template_name, manager)

        return False

    def can_instantiate(self) -> bool:
        """Check if this template can be instantiated"""
        return not self.is_abstract

    def add_validation_rule(self, rule_type: str, field_name: str, **kwargs):
        """Add a validation rule"""
        rule = {
            "type": rule_type,
            "field": field_name,
            **kwargs
        }
        self.validation_rules.append(rule)
    
    def get_grouped_fields(self) -> Dict[str, List[ScriptableObjectField]]:
        """Get fields organized by group"""
        groups = {}
        for field in self.fields:
            group = field.group or "General"
            if group not in groups:
                groups[group] = []
            groups[group].append(field)
        return groups
    
    def generate_python_code(self) -> str:
        """Generate Python code for this template"""
        code_lines = [
            f'"""',
            f'{self.name} - {self.description}',
            f'Generated scriptable object template',
            f'"""',
            '',
            'from core.scriptable_objects.instance import ScriptableObjectInstance',
            '',
            f'class {self.name}(ScriptableObjectInstance):',
            f'    """',
            f'    {self.description}',
            f'    """',
            '',
            f'    def __init__(self, **kwargs):',
            f'        super().__init__("{self.name}", **kwargs)',
            ''
        ]
        
        # Add field initialization
        for field in self.fields:
            default_val = repr(field.get_default_value())
            code_lines.append(f'        self.{field.name} = kwargs.get("{field.name}", {default_val})')
        
        code_lines.extend(['', '    def _ready(self):', '        """Called when the object is ready"""', '        pass', ''])
        
        # Add base code if provided
        if self.base_code.strip():
            code_lines.extend(['    # Custom code', ''])
            for line in self.base_code.split('\n'):
                code_lines.append(f'    {line}')
        
        # Add field-specific code snippets
        for field in self.fields:
            if field.code_snippet.strip():
                code_lines.extend([f'', f'    # Code for {field.name}'])
                for line in field.code_snippet.split('\n'):
                    code_lines.append(f'    {line}')
        
        return '\n'.join(code_lines)
    
    def validate_instance_data(self, data: Dict[str, Any], manager=None) -> List[str]:
        """Validate instance data against this template"""
        errors = []

        # Get all fields including inherited ones
        all_fields = self.get_all_fields(manager) if manager else self.fields

        for field in all_fields:
            if field.name in data:
                value = data[field.name]

                # Basic type validation
                if not field.validate_value(value):
                    errors.append(f"Invalid value for field '{field.name}': {value}")

                # Range validation for numeric types
                if field.min_value is not None and isinstance(value, (int, float)):
                    if value < field.min_value:
                        errors.append(f"Value for '{field.name}' ({value}) is below minimum ({field.min_value})")

                if field.max_value is not None and isinstance(value, (int, float)):
                    if value > field.max_value:
                        errors.append(f"Value for '{field.name}' ({value}) is above maximum ({field.max_value})")

            elif field.required:
                errors.append(f"Required field '{field.name}' is missing")

        # Apply custom validation rules
        for rule in self.validation_rules:
            error = self._apply_validation_rule(rule, data)
            if error:
                errors.append(error)

        return errors

    def _apply_validation_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> Optional[str]:
        """Apply a single validation rule"""
        rule_type = rule.get("type")
        field_name = rule.get("field")

        if field_name not in data:
            return None

        value = data[field_name]

        if rule_type == "unique":
            # This would need to be implemented with access to all instances
            pass
        elif rule_type == "regex":
            import re
            pattern = rule.get("pattern", "")
            if pattern and isinstance(value, str):
                if not re.match(pattern, value):
                    return f"Field '{field_name}' does not match required pattern"
        elif rule_type == "custom":
            # Custom validation function
            func = rule.get("function")
            if func and callable(func):
                if not func(value):
                    return f"Field '{field_name}' failed custom validation"

        return None
    
    def create_default_instance_data(self) -> Dict[str, Any]:
        """Create default instance data for this template"""
        data = {}
        for field in self.fields:
            data[field.name] = field.get_default_value()
        return data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "fields": [field.to_dict() for field in self.fields],
            "base_code": self.base_code,
            "icon_path": self.icon_path,
            "category": self.category,
            "version": self.version,
            "metadata": self.metadata,
            "parent_template": self.parent_template,
            "is_abstract": self.is_abstract,
            "validation_rules": self.validation_rules
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptableObjectTemplate':
        """Create template from dictionary"""
        template = cls(
            name=data.get("name", ""),
            description=data.get("description", "")
        )
        
        # Load fields
        for field_data in data.get("fields", []):
            field = ScriptableObjectField.from_dict(field_data)
            template.add_field(field)
        
        template.base_code = data.get("base_code", "")
        template.icon_path = data.get("icon_path", "")
        template.category = data.get("category", "")
        template.version = data.get("version", "1.0.0")
        template.metadata = data.get("metadata", {})
        template.parent_template = data.get("parent_template")
        template.is_abstract = data.get("is_abstract", False)
        template.validation_rules = data.get("validation_rules", [])
        
        return template
    
    def save_to_file(self, file_path: str):
        """Save template to JSON file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['ScriptableObjectTemplate']:
        """Load template from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading template from {file_path}: {e}")
            return None
    
    def generate_python_file(self, output_path: str):
        """Generate and save Python file for this template"""
        code = self.generate_python_code()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
