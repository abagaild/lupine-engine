"""
LSC Export System - Handles export variables for inspector integration
Manages export variables, groups, and type hints for the game engine editor
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ExportType(Enum):
    """Types of export variables"""
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    COLOR = "color"
    VECTOR2 = "vector2"
    VECTOR3 = "vector3"
    NODE_PATH = "node_path"
    FILE_PATH = "file_path"
    TEXTURE = "texture"
    AUDIO = "audio"
    SCENE = "scene"
    SCRIPT = "script"
    ENUM = "enum"
    RANGE = "range"
    MULTILINE = "multiline"
    PLACEHOLDER = "placeholder"


@dataclass
class ExportVariable:
    """Represents an exported variable"""
    name: str
    type_hint: str
    value: Any
    export_type: Optional[ExportType] = None
    export_hint: Optional[str] = None
    group: Optional[str] = None
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    enum_values: Optional[List[str]] = None
    file_extensions: Optional[List[str]] = None
    placeholder_text: Optional[str] = None


@dataclass
class ExportGroup:
    """Represents an export group"""
    name: str
    prefix: Optional[str] = None
    variables: List[ExportVariable] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []


class ExportSystem:
    """Manages export variables and groups for LSC scripts"""
    
    def __init__(self):
        self.variables: Dict[str, ExportVariable] = {}
        self.groups: Dict[str, ExportGroup] = {}
        self.current_group: Optional[str] = None
    
    def add_export_group(self, name: str, prefix: Optional[str] = None) -> None:
        """Add an export group"""
        self.groups[name] = ExportGroup(name, prefix)
        self.current_group = name
    
    def add_export_variable(self, name: str, type_hint: str, value: Any,
                          export_type: Optional[str] = None,
                          export_hint: Optional[str] = None) -> None:
        """Add an export variable"""
        # Parse export type
        parsed_export_type = None
        if export_type:
            try:
                parsed_export_type = ExportType(export_type.lower())
            except ValueError:
                parsed_export_type = None
        
        # Parse export hint for specific types
        min_value = None
        max_value = None
        step = None
        enum_values = None
        file_extensions = None
        placeholder_text = None
        
        if export_hint:
            if parsed_export_type == ExportType.RANGE:
                # Parse range hint: "min,max" or "min,max,step"
                parts = export_hint.split(',')
                if len(parts) >= 2:
                    try:
                        min_value = float(parts[0])
                        max_value = float(parts[1])
                        if len(parts) >= 3:
                            step = float(parts[2])
                    except ValueError:
                        pass
            
            elif parsed_export_type == ExportType.ENUM:
                # Parse enum hint: "value1,value2,value3"
                enum_values = [v.strip() for v in export_hint.split(',')]
            
            elif parsed_export_type == ExportType.FILE_PATH:
                # Parse file extensions: "*.png,*.jpg,*.gif"
                file_extensions = [ext.strip() for ext in export_hint.split(',')]
            
            elif parsed_export_type == ExportType.PLACEHOLDER:
                # Placeholder text
                placeholder_text = export_hint
        
        # Create export variable
        export_var = ExportVariable(
            name=name,
            type_hint=type_hint,
            value=value,
            export_type=parsed_export_type,
            export_hint=export_hint,
            group=self.current_group,
            min_value=min_value,
            max_value=max_value,
            step=step,
            enum_values=enum_values,
            file_extensions=file_extensions,
            placeholder_text=placeholder_text
        )
        
        # Add to variables
        self.variables[name] = export_var
        
        # Add to current group if exists
        if self.current_group and self.current_group in self.groups:
            self.groups[self.current_group].variables.append(export_var)
    
    def get_export_variable(self, name: str) -> Optional[ExportVariable]:
        """Get export variable by name"""
        return self.variables.get(name)
    
    def get_export_group(self, name: str) -> Optional[ExportGroup]:
        """Get export group by name"""
        return self.groups.get(name)
    
    def get_all_variables(self) -> List[ExportVariable]:
        """Get all export variables"""
        return list(self.variables.values())
    
    def get_all_groups(self) -> List[ExportGroup]:
        """Get all export groups"""
        return list(self.groups.values())
    
    def get_variables_in_group(self, group_name: str) -> List[ExportVariable]:
        """Get all variables in a specific group"""
        group = self.groups.get(group_name)
        if group:
            return group.variables
        return []
    
    def get_ungrouped_variables(self) -> List[ExportVariable]:
        """Get variables not in any group"""
        return [var for var in self.variables.values() if var.group is None]
    
    def update_variable_value(self, name: str, value: Any) -> bool:
        """Update the value of an export variable"""
        if name in self.variables:
            self.variables[name].value = value
            return True
        return False
    
    def validate_variable_value(self, name: str, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a value for an export variable"""
        var = self.variables.get(name)
        if not var:
            return False, "Variable not found"
        
        # Type validation
        if var.type_hint == "int" and not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                return False, "Value must be an integer"
        
        elif var.type_hint == "float" and not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return False, "Value must be a number"
        
        elif var.type_hint == "string" and not isinstance(value, str):
            value = str(value)
        
        elif var.type_hint == "bool" and not isinstance(value, bool):
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')
            else:
                value = bool(value)
        
        # Range validation
        if var.export_type == ExportType.RANGE:
            if var.min_value is not None and value < var.min_value:
                return False, f"Value must be >= {var.min_value}"
            if var.max_value is not None and value > var.max_value:
                return False, f"Value must be <= {var.max_value}"
        
        # Enum validation
        if var.export_type == ExportType.ENUM and var.enum_values:
            if str(value) not in var.enum_values:
                return False, f"Value must be one of: {', '.join(var.enum_values)}"
        
        return True, None
    
    def get_inspector_data(self) -> Dict[str, Any]:
        """Get data formatted for the inspector"""
        inspector_data = {
            'groups': [],
            'ungrouped': []
        }
        
        # Add groups
        for group in self.groups.values():
            group_data = {
                'name': group.name,
                'prefix': group.prefix,
                'variables': []
            }
            
            for var in group.variables:
                var_data = self._variable_to_inspector_data(var)
                group_data['variables'].append(var_data)
            
            inspector_data['groups'].append(group_data)
        
        # Add ungrouped variables
        for var in self.get_ungrouped_variables():
            var_data = self._variable_to_inspector_data(var)
            inspector_data['ungrouped'].append(var_data)
        
        return inspector_data
    
    def _variable_to_inspector_data(self, var: ExportVariable) -> Dict[str, Any]:
        """Convert export variable to inspector data format"""
        data = {
            'name': var.name,
            'type': var.type_hint,
            'value': var.value,
            'description': var.description
        }
        
        if var.export_type:
            data['export_type'] = var.export_type.value
        
        if var.export_hint:
            data['export_hint'] = var.export_hint
        
        if var.min_value is not None:
            data['min_value'] = var.min_value
        
        if var.max_value is not None:
            data['max_value'] = var.max_value
        
        if var.step is not None:
            data['step'] = var.step
        
        if var.enum_values:
            data['enum_values'] = var.enum_values
        
        if var.file_extensions:
            data['file_extensions'] = var.file_extensions
        
        if var.placeholder_text:
            data['placeholder_text'] = var.placeholder_text
        
        return data
    
    def clear(self) -> None:
        """Clear all export data"""
        self.variables.clear()
        self.groups.clear()
        self.current_group = None
    
    def remove_variable(self, name: str) -> bool:
        """Remove an export variable"""
        if name in self.variables:
            var = self.variables[name]
            
            # Remove from group if it's in one
            if var.group and var.group in self.groups:
                group = self.groups[var.group]
                if var in group.variables:
                    group.variables.remove(var)
            
            # Remove from variables
            del self.variables[name]
            return True
        
        return False
    
    def remove_group(self, name: str) -> bool:
        """Remove an export group and all its variables"""
        if name in self.groups:
            group = self.groups[name]
            
            # Remove all variables in the group
            for var in group.variables[:]:  # Copy list to avoid modification during iteration
                self.remove_variable(var.name)
            
            # Remove the group
            del self.groups[name]
            
            # Reset current group if it was the removed one
            if self.current_group == name:
                self.current_group = None
            
            return True
        
        return False
