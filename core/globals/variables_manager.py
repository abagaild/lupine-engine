"""
Variables Manager for Lupine Engine
Manages global variables with type safety and easy access
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from enum import Enum
import threading


class VariableType(Enum):
    """Supported variable types"""
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    COLOR = "color"
    VECTOR2 = "vector2"
    VECTOR3 = "vector3"
    PATH = "path"
    RESOURCE = "resource"


class GlobalVariable:
    """Represents a global variable definition"""
    
    def __init__(self, name: str, var_type: VariableType, value: Any, description: str = ""):
        self.name = name
        self.type = var_type
        self.value = value
        self.description = description
        self.default_value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "description": self.description,
            "default_value": self.default_value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalVariable':
        """Create from dictionary"""
        var_type = VariableType(data["type"])
        return cls(
            name=data["name"],
            var_type=var_type,
            value=data["value"],
            description=data.get("description", "")
        )
    
    def validate_value(self, value: Any) -> bool:
        """Validate if a value is compatible with this variable's type"""
        try:
            self._convert_value(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def set_value(self, value: Any) -> bool:
        """Set the variable value with type validation"""
        try:
            self.value = self._convert_value(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _convert_value(self, value: Any) -> Any:
        """Convert value to the appropriate type"""
        if self.type == VariableType.INT:
            return int(value)
        elif self.type == VariableType.FLOAT:
            return float(value)
        elif self.type == VariableType.STRING:
            return str(value)
        elif self.type == VariableType.BOOL:
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return bool(value)
        elif self.type == VariableType.COLOR:
            # Expect [r, g, b, a] format
            if isinstance(value, (list, tuple)) and len(value) >= 3:
                r, g, b = value[0], value[1], value[2]
                a = value[3] if len(value) > 3 else 1.0
                return [float(r), float(g), float(b), float(a)]
            else:
                raise ValueError("Color must be [r, g, b] or [r, g, b, a]")
        elif self.type == VariableType.VECTOR2:
            # Expect [x, y] format
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                return [float(value[0]), float(value[1])]
            else:
                raise ValueError("Vector2 must be [x, y]")
        elif self.type == VariableType.VECTOR3:
            # Expect [x, y, z] format
            if isinstance(value, (list, tuple)) and len(value) >= 3:
                return [float(value[0]), float(value[1]), float(value[2])]
            else:
                raise ValueError("Vector3 must be [x, y, z]")
        elif self.type == VariableType.PATH:
            return str(value)
        elif self.type == VariableType.RESOURCE:
            return str(value)
        else:
            raise ValueError(f"Unknown variable type: {self.type}")
    
    def reset_to_default(self):
        """Reset variable to its default value"""
        self.value = self.default_value


class VariablesManager:
    """Manages global variables for the project"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.variables: Dict[str, GlobalVariable] = {}
        self._lock = threading.RLock()
        
        # Load existing variables
        self.load_variables()
    
    def add_variable(self, name: str, var_type: VariableType, value: Any, description: str = "") -> bool:
        """Add a new global variable"""
        with self._lock:
            if name in self.variables:
                return False
            
            try:
                variable = GlobalVariable(name, var_type, value, description)
                # Validate the initial value
                if not variable.validate_value(value):
                    return False
                
                variable.set_value(value)
                self.variables[name] = variable
                return True
                
            except Exception as e:
                print(f"Failed to add variable {name}: {e}")
                return False
    
    def remove_variable(self, name: str) -> bool:
        """Remove a global variable"""
        with self._lock:
            if name not in self.variables:
                return False
            
            del self.variables[name]
            return True
    
    def update_variable(self, name: str, var_type: Optional[VariableType] = None, 
                       value: Optional[Any] = None, description: Optional[str] = None) -> bool:
        """Update a global variable"""
        with self._lock:
            if name not in self.variables:
                return False
            
            variable = self.variables[name]
            
            try:
                if var_type is not None:
                    variable.type = var_type
                    # Re-validate current value with new type
                    if not variable.validate_value(variable.value):
                        # Reset to a default value for the new type
                        default_values = {
                            VariableType.INT: 0,
                            VariableType.FLOAT: 0.0,
                            VariableType.STRING: "",
                            VariableType.BOOL: False,
                            VariableType.COLOR: [1.0, 1.0, 1.0, 1.0],
                            VariableType.VECTOR2: [0.0, 0.0],
                            VariableType.VECTOR3: [0.0, 0.0, 0.0],
                            VariableType.PATH: "",
                            VariableType.RESOURCE: ""
                        }
                        variable.set_value(default_values[var_type])
                
                if value is not None:
                    if not variable.set_value(value):
                        return False
                
                if description is not None:
                    variable.description = description
                
                return True
                
            except Exception as e:
                print(f"Failed to update variable {name}: {e}")
                return False
    
    def get_variable(self, name: str) -> Optional[GlobalVariable]:
        """Get a global variable by name"""
        with self._lock:
            return self.variables.get(name)
    
    def get_value(self, name: str) -> Optional[Any]:
        """Get the value of a global variable"""
        with self._lock:
            variable = self.variables.get(name)
            return variable.value if variable else None
    
    def set_value(self, name: str, value: Any) -> bool:
        """Set the value of a global variable"""
        with self._lock:
            variable = self.variables.get(name)
            if variable:
                return variable.set_value(value)
            return False
    
    def get_all_variables(self) -> List[GlobalVariable]:
        """Get all global variables"""
        with self._lock:
            return list(self.variables.values())
    
    def reset_all_to_defaults(self):
        """Reset all variables to their default values"""
        with self._lock:
            for variable in self.variables.values():
                variable.reset_to_default()
    
    def save_variables(self):
        """Save variable definitions to project file"""
        try:
            config_file = self.project_path / "project.json"
            
            # Load existing project config
            config = {}
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
            
            # Update variables section
            if "globals" not in config:
                config["globals"] = {}
            
            config["globals"]["variables"] = [
                variable.to_dict() for variable in self.variables.values()
            ]
            
            # Save back to file
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to save variables: {e}")
            return False
    
    def load_variables(self):
        """Load variable definitions from project file"""
        try:
            config_file = self.project_path / "project.json"
            if not config_file.exists():
                return
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            variables_data = config.get("globals", {}).get("variables", [])
            
            for variable_data in variables_data:
                variable = GlobalVariable.from_dict(variable_data)
                self.variables[variable.name] = variable
            
        except Exception as e:
            print(f"Failed to load variables: {e}")


# Global variables manager instance
_variables_manager: Optional[VariablesManager] = None


def get_variables_manager() -> Optional[VariablesManager]:
    """Get the global variables manager instance"""
    return _variables_manager


def initialize_variables_manager(project_path: str) -> VariablesManager:
    """Initialize the global variables manager"""
    global _variables_manager
    _variables_manager = VariablesManager(project_path)
    return _variables_manager


def get_global_var(name: str) -> Optional[Any]:
    """Get a global variable value by name (convenience function)"""
    if _variables_manager:
        return _variables_manager.get_value(name)
    return None


def set_global_var(name: str, value: Any) -> bool:
    """Set a global variable value by name (convenience function)"""
    if _variables_manager:
        return _variables_manager.set_value(name, value)
    return False
