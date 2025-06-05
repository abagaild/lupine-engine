"""
Enhanced Prefab System for Lupine Engine
Supports visual scripting, events, and complex prefab definitions
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from ..json_utils import safe_json_dump, safe_json_dumps


class PrefabType(Enum):
    """Types of prefabs"""
    NODE = "node"           # Single node prefab
    SCENE = "scene"         # Multi-node scene prefab
    EVENT = "event"         # Event/trigger prefab
    ENTITY = "entity"       # Game entity (NPC, monster, etc.)
    ITEM = "item"          # Item/collectible prefab
    INTERACTIVE = "interactive"  # Interactive object prefab


class VisualScriptBlockType(Enum):
    """Types of visual script blocks"""
    ACTION = "action"       # Performs an action
    CONDITION = "condition" # Boolean condition
    EVENT = "event"        # Event trigger
    VARIABLE = "variable"   # Variable operation
    FLOW = "flow"          # Control flow (if, loop, etc.)
    FUNCTION = "function"   # Function definition/call
    CLASS = "class"        # Class definition
    LOOP = "loop"          # Loop constructs
    MATH = "math"          # Mathematical operations
    STRING = "string"      # String operations
    LIST = "list"          # List/array operations
    DICT = "dict"          # Dictionary operations
    INPUT = "input"        # Input nodes
    OUTPUT = "output"      # Output nodes
    CUSTOM = "custom"      # Custom user-defined block


@dataclass
class VisualScriptInput:
    """Input parameter for a visual script block"""
    name: str
    type: str  # "string", "number", "boolean", "node", "scene", "variable", "exec", etc.
    default_value: Any = None
    description: str = ""
    required: bool = True
    options: Optional[List[str]] = None  # For dropdown inputs
    is_execution_pin: bool = False  # True for execution flow pins
    multiple_connections: bool = False  # Allow multiple input connections
    color: str = "#FFFFFF"  # Color for the connection pin

    def __post_init__(self):
        """Set default colors based on type"""
        if not hasattr(self, 'color') or self.color == "#FFFFFF":
            self.color = self.get_type_color()

    def get_type_color(self) -> str:
        """Get color for this input type"""
        type_colors = {
            "exec": "#FFFFFF",      # White for execution
            "string": "#FF69B4",    # Pink for strings
            "number": "#00FF00",    # Green for numbers
            "boolean": "#FF0000",   # Red for booleans
            "node": "#0080FF",      # Blue for nodes
            "scene": "#8000FF",     # Purple for scenes
            "variable": "#FFFF00",  # Yellow for variables
            "list": "#FF8000",      # Orange for lists
            "dict": "#00FFFF",      # Cyan for dictionaries
            "vector2": "#8000FF",   # Purple for vectors
            "color": "#FF8000",     # Orange for colors
            "path": "#80FF80",      # Light green for paths
            "any": "#808080"        # Gray for any type
        }
        return type_colors.get(self.type, "#808080")


@dataclass
class VisualScriptOutput:
    """Output parameter for a visual script block"""
    name: str
    type: str  # "string", "number", "boolean", "node", "scene", "variable", "exec", etc.
    description: str = ""
    is_execution_pin: bool = False  # True for execution flow pins
    multiple_connections: bool = True  # Allow multiple output connections
    color: str = "#FFFFFF"  # Color for the connection pin

    def __post_init__(self):
        """Set default colors based on type"""
        if not hasattr(self, 'color') or self.color == "#FFFFFF":
            self.color = self.get_type_color()

    def get_type_color(self) -> str:
        """Get color for this output type"""
        type_colors = {
            "exec": "#FFFFFF",      # White for execution
            "string": "#FF69B4",    # Pink for strings
            "number": "#00FF00",    # Green for numbers
            "boolean": "#FF0000",   # Red for booleans
            "node": "#0080FF",      # Blue for nodes
            "scene": "#8000FF",     # Purple for scenes
            "variable": "#FFFF00",  # Yellow for variables
            "list": "#FF8000",      # Orange for lists
            "dict": "#00FFFF",      # Cyan for dictionaries
            "vector2": "#8000FF",   # Purple for vectors
            "color": "#FF8000",     # Orange for colors
            "path": "#80FF80",      # Light green for paths
            "any": "#808080"        # Gray for any type
        }
        return type_colors.get(self.type, "#808080")


@dataclass
class VisualScriptBlock:
    """Definition of a visual script block"""
    id: str
    name: str
    category: str
    block_type: VisualScriptBlockType
    description: str
    inputs: List[VisualScriptInput] = field(default_factory=list)
    outputs: List[VisualScriptOutput] = field(default_factory=list)
    code_template: str = ""  # Python code template with placeholders
    icon: str = ""
    color: str = "#4A90E2"  # Block color in visual editor


@dataclass
class EventDefinition:
    """Definition of an event that can be triggered"""
    name: str
    description: str
    parameters: List[VisualScriptInput] = field(default_factory=list)
    default_script: str = ""  # Default script code for this event


@dataclass
class PrefabProperty:
    """Property definition for a prefab"""
    name: str
    type: str  # "string", "number", "boolean", "color", "path", "nodepath", etc.
    default_value: Any = None
    description: str = ""
    group: str = ""  # Property group for organization
    export: bool = True  # Whether this property is exported to inspector
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[str]] = None  # For enum/dropdown properties


class EnhancedPrefab:
    """Enhanced prefab with visual scripting support"""
    
    def __init__(self, name: str, prefab_type: PrefabType = PrefabType.NODE):
        self.id = str(uuid.uuid4())
        self.name = name
        self.prefab_type = prefab_type
        self.description = ""
        self.category = "Custom"
        self.icon = ""
        self.preview_image = ""
        
        # Node structure
        self.base_node_type = "Node2D"
        self.node_structure = {}  # Complete node hierarchy
        
        # Properties
        self.properties: List[PrefabProperty] = []
        self.property_groups: Dict[str, str] = {}  # group_name -> description
        
        # Events and scripting
        self.events: List[EventDefinition] = []
        self.visual_script_blocks: List[VisualScriptBlock] = []
        self.visual_script_path: Optional[str] = None  # Path to visual script file
        self.default_script = ""
        
        # Metadata
        self.tags: List[str] = []
        self.version = "1.0.0"
        self.author = ""
        self.created_at = ""
        self.modified_at = ""
        
        # Dependencies
        self.required_nodes: List[str] = []
        self.required_scripts: List[str] = []
        self.required_assets: List[str] = []
    
    def add_property(self, name: str, prop_type: str, default_value: Any = None, 
                    description: str = "", group: str = "", **kwargs) -> PrefabProperty:
        """Add a property to the prefab"""
        prop = PrefabProperty(
            name=name,
            type=prop_type,
            default_value=default_value,
            description=description,
            group=group,
            **kwargs
        )
        self.properties.append(prop)
        return prop
    
    def add_event(self, name: str, description: str = "", 
                 parameters: Optional[List[VisualScriptInput]] = None) -> EventDefinition:
        """Add an event to the prefab"""
        event = EventDefinition(
            name=name,
            description=description,
            parameters=parameters or []
        )
        self.events.append(event)
        return event
    
    def add_visual_script_block(self, block: VisualScriptBlock):
        """Add a visual script block to the prefab"""
        self.visual_script_blocks.append(block)
    
    def create_instance(self, instance_name: Optional[str] = None, 
                       property_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an instance of this prefab"""
        instance_name = instance_name or self.name
        
        # Start with base node structure
        instance = dict(self.node_structure)
        instance["name"] = instance_name
        instance["prefab_id"] = self.id
        instance["prefab_name"] = self.name
        
        # Apply default property values
        instance_properties = {}
        for prop in self.properties:
            if prop.export:
                instance_properties[prop.name] = prop.default_value
        
        # Apply property overrides
        if property_overrides:
            instance_properties.update(property_overrides)
        
        instance["prefab_properties"] = instance_properties
        
        # Add event handlers
        if self.events:
            instance["prefab_events"] = [event.name for event in self.events]
        
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert prefab to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "prefab_type": self.prefab_type.value,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "preview_image": self.preview_image,
            "base_node_type": self.base_node_type,
            "node_structure": self.node_structure,
            "properties": [
                {
                    "name": prop.name,
                    "type": prop.type,
                    "default_value": prop.default_value,
                    "description": prop.description,
                    "group": prop.group,
                    "export": prop.export,
                    "min_value": prop.min_value,
                    "max_value": prop.max_value,
                    "step": prop.step,
                    "options": prop.options
                }
                for prop in self.properties
            ],
            "property_groups": self.property_groups,
            "events": [
                {
                    "name": event.name,
                    "description": event.description,
                    "parameters": [
                        {
                            "name": param.name,
                            "type": param.type,
                            "default_value": param.default_value,
                            "description": param.description,
                            "required": param.required,
                            "options": param.options
                        }
                        for param in event.parameters
                    ],
                    "default_script": event.default_script
                }
                for event in self.events
            ],
            "visual_script_blocks": [
                {
                    "id": block.id,
                    "name": block.name,
                    "category": block.category,
                    "block_type": block.block_type.value,
                    "description": block.description,
                    "inputs": [
                        {
                            "name": inp.name,
                            "type": inp.type,
                            "default_value": inp.default_value,
                            "description": inp.description,
                            "required": inp.required,
                            "options": inp.options
                        }
                        for inp in block.inputs
                    ],
                    "outputs": [
                        {
                            "name": out.name,
                            "type": out.type,
                            "description": out.description
                        }
                        for out in block.outputs
                    ],
                    "code_template": block.code_template,
                    "icon": block.icon,
                    "color": block.color
                }
                for block in self.visual_script_blocks
            ],
            "visual_script_path": self.visual_script_path,
            "default_script": self.default_script,
            "tags": self.tags,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "required_nodes": self.required_nodes,
            "required_scripts": self.required_scripts,
            "required_assets": self.required_assets
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedPrefab":
        """Create prefab from dictionary"""
        prefab = cls(data["name"], PrefabType(data["prefab_type"]))
        prefab.id = data.get("id", str(uuid.uuid4()))
        prefab.description = data.get("description", "")
        prefab.category = data.get("category", "Custom")
        prefab.icon = data.get("icon", "")
        prefab.preview_image = data.get("preview_image", "")
        prefab.base_node_type = data.get("base_node_type", "Node2D")
        prefab.node_structure = data.get("node_structure", {})
        
        # Load properties
        for prop_data in data.get("properties", []):
            prop = PrefabProperty(**prop_data)
            prefab.properties.append(prop)
        
        prefab.property_groups = data.get("property_groups", {})
        
        # Load events
        for event_data in data.get("events", []):
            event = EventDefinition(
                name=event_data["name"],
                description=event_data.get("description", ""),
                parameters=[
                    VisualScriptInput(**param_data)
                    for param_data in event_data.get("parameters", [])
                ],
                default_script=event_data.get("default_script", "")
            )
            prefab.events.append(event)
        
        # Load visual script blocks
        for block_data in data.get("visual_script_blocks", []):
            block = VisualScriptBlock(
                id=block_data["id"],
                name=block_data["name"],
                category=block_data["category"],
                block_type=VisualScriptBlockType(block_data["block_type"]),
                description=block_data.get("description", ""),
                inputs=[
                    VisualScriptInput(**inp_data)
                    for inp_data in block_data.get("inputs", [])
                ],
                outputs=[
                    VisualScriptOutput(**out_data)
                    for out_data in block_data.get("outputs", [])
                ],
                code_template=block_data.get("code_template", ""),
                icon=block_data.get("icon", ""),
                color=block_data.get("color", "#4A90E2")
            )
            prefab.visual_script_blocks.append(block)

        prefab.visual_script_path = data.get("visual_script_path")
        prefab.default_script = data.get("default_script", "")
        prefab.tags = data.get("tags", [])
        prefab.version = data.get("version", "1.0.0")
        prefab.author = data.get("author", "")
        prefab.created_at = data.get("created_at", "")
        prefab.modified_at = data.get("modified_at", "")
        prefab.required_nodes = data.get("required_nodes", [])
        prefab.required_scripts = data.get("required_scripts", [])
        prefab.required_assets = data.get("required_assets", [])
        
        return prefab
    
    def save_to_file(self, file_path: str):
        """Save prefab to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            safe_json_dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "EnhancedPrefab":
        """Load prefab from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
