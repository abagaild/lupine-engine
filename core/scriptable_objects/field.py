"""
Scriptable Object Field Definition
Defines the structure and behavior of individual fields in scriptable objects
"""

from typing import Any, Dict, Optional, Callable, List
from enum import Enum


class FieldType(Enum):
    """Supported field types for scriptable objects"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    COLOR = "color"
    PATH = "path"
    IMAGE = "image"
    SPRITE_SHEET = "sprite_sheet"
    NODEPATH = "nodepath"
    VECTOR2 = "vector2"
    VECTOR3 = "vector3"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"
    RANGE = "range"
    REFERENCE = "reference"
    CURVE = "curve"
    AUDIO = "audio"


class ScriptableObjectField:
    """Represents a field in a scriptable object template"""

    def __init__(self, name: str, field_type: FieldType, default_value: Any = None,
                 description: str = "", group: str = "", code_snippet: str = ""):
        self.name = name
        self.field_type = field_type
        self.default_value = default_value
        self.description = description
        self.group = group  # For organizing fields into groups
        self.code_snippet = code_snippet  # Custom code for this field
        self.validation_func: Optional[Callable] = None
        self.metadata: Dict[str, Any] = {}

        # Enhanced field properties
        self.enum_values: List[str] = []  # For ENUM type
        self.reference_template: str = ""  # For REFERENCE type
        self.min_value: Optional[float] = None  # For numeric types and RANGE
        self.max_value: Optional[float] = None  # For numeric types and RANGE
        self.required: bool = False  # Whether field is required
        self.readonly: bool = False  # Whether field is read-only
        self.order: int = 0  # For field ordering
    
    def validate_value(self, value: Any) -> bool:
        """Validate a value against this field's type and constraints"""
        if self.validation_func:
            return self.validation_func(value)
        
        # Basic type validation
        if self.field_type == FieldType.STRING:
            return isinstance(value, str)
        elif self.field_type == FieldType.INT:
            return isinstance(value, int)
        elif self.field_type == FieldType.FLOAT:
            return isinstance(value, (int, float))
        elif self.field_type == FieldType.BOOL:
            return isinstance(value, bool)
        elif self.field_type == FieldType.COLOR:
            # Expect [r, g, b, a] format
            return (isinstance(value, (list, tuple)) and len(value) == 4 and
                    all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in value))
        elif self.field_type == FieldType.PATH:
            return isinstance(value, str)
        elif self.field_type == FieldType.IMAGE:
            return isinstance(value, str)
        elif self.field_type == FieldType.SPRITE_SHEET:
            return isinstance(value, str)
        elif self.field_type == FieldType.NODEPATH:
            return isinstance(value, str)
        elif self.field_type == FieldType.VECTOR2:
            return (isinstance(value, (list, tuple)) and len(value) == 2 and
                    all(isinstance(v, (int, float)) for v in value))
        elif self.field_type == FieldType.VECTOR3:
            return (isinstance(value, (list, tuple)) and len(value) == 3 and
                    all(isinstance(v, (int, float)) for v in value))
        elif self.field_type == FieldType.ARRAY:
            return isinstance(value, list)
        elif self.field_type == FieldType.OBJECT:
            return isinstance(value, dict)
        elif self.field_type == FieldType.ENUM:
            return isinstance(value, str) and (not self.enum_values or value in self.enum_values)
        elif self.field_type == FieldType.RANGE:
            return (isinstance(value, (list, tuple)) and len(value) == 2 and
                    all(isinstance(v, (int, float)) for v in value) and value[0] <= value[1])
        elif self.field_type == FieldType.REFERENCE:
            return isinstance(value, str)  # Reference ID or name
        elif self.field_type == FieldType.CURVE:
            return isinstance(value, (list, dict))  # Curve data structure
        elif self.field_type == FieldType.AUDIO:
            return isinstance(value, str)  # Audio file path

        return True
    
    def get_default_value(self) -> Any:
        """Get the default value for this field type"""
        if self.default_value is not None:
            return self.default_value
        
        # Type-specific defaults
        defaults = {
            FieldType.STRING: "",
            FieldType.INT: 0,
            FieldType.FLOAT: 0.0,
            FieldType.BOOL: False,
            FieldType.COLOR: [1.0, 1.0, 1.0, 1.0],
            FieldType.PATH: "",
            FieldType.IMAGE: "",
            FieldType.SPRITE_SHEET: "",
            FieldType.NODEPATH: "",
            FieldType.VECTOR2: [0.0, 0.0],
            FieldType.VECTOR3: [0.0, 0.0, 0.0],
            FieldType.ARRAY: [],
            FieldType.OBJECT: {},
            FieldType.ENUM: self.enum_values[0] if self.enum_values else "",
            FieldType.RANGE: [0.0, 1.0],
            FieldType.REFERENCE: "",
            FieldType.CURVE: {"points": [[0.0, 0.0], [1.0, 1.0]]},
            FieldType.AUDIO: ""
        }
        
        return defaults.get(self.field_type, None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary for serialization"""
        return {
            "name": self.name,
            "type": self.field_type.value,
            "default_value": self.default_value,
            "description": self.description,
            "group": self.group,
            "code_snippet": self.code_snippet,
            "metadata": self.metadata,
            "enum_values": self.enum_values,
            "reference_template": self.reference_template,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "required": self.required,
            "readonly": self.readonly,
            "order": self.order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptableObjectField':
        """Create field from dictionary"""
        field_type = FieldType(data.get("type", "string"))
        field = cls(
            name=data.get("name", ""),
            field_type=field_type,
            default_value=data.get("default_value"),
            description=data.get("description", ""),
            group=data.get("group", ""),
            code_snippet=data.get("code_snippet", "")
        )
        field.metadata = data.get("metadata", {})
        field.enum_values = data.get("enum_values", [])
        field.reference_template = data.get("reference_template", "")
        field.min_value = data.get("min_value")
        field.max_value = data.get("max_value")
        field.required = data.get("required", False)
        field.readonly = data.get("readonly", False)
        field.order = data.get("order", 0)
        return field
    
    def set_validation_func(self, func: Callable[[Any], bool]):
        """Set a custom validation function"""
        self.validation_func = func
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the field"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)
