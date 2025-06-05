"""
Variable Binding System for Lupine Engine UI
Handles binding UI elements to global variables for dynamic updates
"""

from typing import Dict, Any, Optional, Callable, List
from enum import Enum
import re


class BindingType(Enum):
    """Types of variable bindings"""
    DISPLAY = "display"  # Show variable value
    VISIBILITY = "visibility"  # Show/hide based on condition
    ENABLE = "enable"  # Enable/disable based on condition
    COLOR = "color"  # Change color based on value
    SIZE = "size"  # Change size based on value
    PROGRESS = "progress"  # Update progress bar value


class VariableBinding:
    """Represents a binding between a UI element and a global variable"""
    
    def __init__(self, binding_type: BindingType, variable_name: str, 
                 property_name: str, format_string: str = None,
                 condition: str = None, transform_function: str = None):
        self.binding_type = binding_type
        self.variable_name = variable_name
        self.property_name = property_name
        self.format_string = format_string or "{value}"
        self.condition = condition  # For visibility/enable bindings
        self.transform_function = transform_function  # Custom transformation code
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "binding_type": self.binding_type.value,
            "variable_name": self.variable_name,
            "property_name": self.property_name,
            "format_string": self.format_string,
            "condition": self.condition,
            "transform_function": self.transform_function
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableBinding":
        """Create from dictionary"""
        return cls(
            binding_type=BindingType(data["binding_type"]),
            variable_name=data["variable_name"],
            property_name=data["property_name"],
            format_string=data.get("format_string", "{value}"),
            condition=data.get("condition"),
            transform_function=data.get("transform_function")
        )


class VariableBindingManager:
    """Manages variable bindings for UI elements"""
    
    def __init__(self):
        self.bindings: Dict[str, List[VariableBinding]] = {}  # node_id -> bindings
        self.cached_values: Dict[str, Any] = {}  # variable_name -> cached value
        
    def add_binding(self, node_id: str, binding: VariableBinding):
        """Add a variable binding for a node"""
        if node_id not in self.bindings:
            self.bindings[node_id] = []
        self.bindings[node_id].append(binding)
    
    def remove_binding(self, node_id: str, binding: VariableBinding):
        """Remove a variable binding"""
        if node_id in self.bindings:
            self.bindings[node_id].remove(binding)
            if not self.bindings[node_id]:
                del self.bindings[node_id]
    
    def get_bindings(self, node_id: str) -> List[VariableBinding]:
        """Get all bindings for a node"""
        return self.bindings.get(node_id, [])
    
    def update_variable(self, variable_name: str, value: Any) -> List[str]:
        """Update a variable and return list of affected node IDs"""
        self.cached_values[variable_name] = value
        affected_nodes = []
        
        for node_id, bindings in self.bindings.items():
            for binding in bindings:
                if binding.variable_name == variable_name:
                    affected_nodes.append(node_id)
                    break
        
        return affected_nodes
    
    def evaluate_binding(self, binding: VariableBinding, node_data: Dict[str, Any]) -> Any:
        """Evaluate a binding and return the new property value"""
        variable_value = self.cached_values.get(binding.variable_name)
        
        if variable_value is None:
            return None
        
        try:
            if binding.binding_type == BindingType.DISPLAY:
                return self._evaluate_display_binding(binding, variable_value)
            elif binding.binding_type == BindingType.VISIBILITY:
                return self._evaluate_visibility_binding(binding, variable_value)
            elif binding.binding_type == BindingType.ENABLE:
                return self._evaluate_enable_binding(binding, variable_value)
            elif binding.binding_type == BindingType.COLOR:
                return self._evaluate_color_binding(binding, variable_value)
            elif binding.binding_type == BindingType.SIZE:
                return self._evaluate_size_binding(binding, variable_value)
            elif binding.binding_type == BindingType.PROGRESS:
                return self._evaluate_progress_binding(binding, variable_value, node_data)
        except Exception as e:
            print(f"Error evaluating binding: {e}")
            return None
    
    def _evaluate_display_binding(self, binding: VariableBinding, value: Any) -> str:
        """Evaluate a display binding"""
        if binding.transform_function:
            # Execute custom transform function
            try:
                local_vars = {"value": value}
                exec(binding.transform_function, {}, local_vars)
                value = local_vars.get("result", value)
            except Exception as e:
                print(f"Error in transform function: {e}")
        
        # Apply format string
        try:
            return binding.format_string.format(value=value)
        except:
            return str(value)
    
    def _evaluate_visibility_binding(self, binding: VariableBinding, value: Any) -> bool:
        """Evaluate a visibility binding"""
        if not binding.condition:
            return bool(value)
        
        try:
            # Replace {value} in condition with actual value
            condition = binding.condition.replace("{value}", str(value))
            # Simple condition evaluation (can be expanded)
            return eval(condition, {"__builtins__": {}}, {"value": value})
        except:
            return bool(value)
    
    def _evaluate_enable_binding(self, binding: VariableBinding, value: Any) -> bool:
        """Evaluate an enable binding"""
        return self._evaluate_visibility_binding(binding, value)
    
    def _evaluate_color_binding(self, binding: VariableBinding, value: Any) -> List[float]:
        """Evaluate a color binding"""
        # This could be expanded to support color gradients based on value ranges
        if isinstance(value, (int, float)):
            # Simple red-to-green gradient based on 0-1 range
            normalized = max(0, min(1, value))
            red = 1.0 - normalized
            green = normalized
            return [red, green, 0.0, 1.0]
        return [1.0, 1.0, 1.0, 1.0]  # Default white
    
    def _evaluate_size_binding(self, binding: VariableBinding, value: Any) -> List[float]:
        """Evaluate a size binding"""
        if isinstance(value, (int, float)):
            # Scale size based on value
            scale = max(0.1, min(2.0, value))
            return [100 * scale, 30 * scale]  # Base size scaled
        return [100, 30]  # Default size
    
    def _evaluate_progress_binding(self, binding: VariableBinding, value: Any, node_data: Dict[str, Any]) -> float:
        """Evaluate a progress binding"""
        if isinstance(value, (int, float)):
            min_val = node_data.get("min_value", 0)
            max_val = node_data.get("max_value", 100)
            # Clamp value to range
            return max(min_val, min(max_val, value))
        return 0.0


# Common binding templates
BINDING_TEMPLATES = {
    "health_display": {
        "type": BindingType.DISPLAY,
        "format": "Health: {value}",
        "description": "Display health value as text"
    },
    "health_bar": {
        "type": BindingType.PROGRESS,
        "description": "Update health bar progress"
    },
    "score_display": {
        "type": BindingType.DISPLAY,
        "format": "Score: {value:,}",
        "description": "Display score with comma formatting"
    },
    "conditional_visibility": {
        "type": BindingType.VISIBILITY,
        "condition": "{value} > 0",
        "description": "Show only when value is greater than 0"
    },
    "button_enable": {
        "type": BindingType.ENABLE,
        "condition": "{value} != null",
        "description": "Enable button when value is not null"
    }
}


def create_binding_from_template(template_name: str, variable_name: str, property_name: str) -> Optional[VariableBinding]:
    """Create a binding from a template"""
    template = BINDING_TEMPLATES.get(template_name)
    if not template:
        return None
    
    return VariableBinding(
        binding_type=template["type"],
        variable_name=variable_name,
        property_name=property_name,
        format_string=template.get("format", "{value}"),
        condition=template.get("condition")
    )


# Global binding manager instance
_binding_manager = None


def get_binding_manager() -> VariableBindingManager:
    """Get the global binding manager instance"""
    global _binding_manager
    if _binding_manager is None:
        _binding_manager = VariableBindingManager()
    return _binding_manager


def initialize_binding_manager() -> VariableBindingManager:
    """Initialize a new binding manager"""
    global _binding_manager
    _binding_manager = VariableBindingManager()
    return _binding_manager
