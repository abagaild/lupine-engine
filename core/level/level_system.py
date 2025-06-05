"""
Level System for Lupine Engine
RPG Maker-style level editing with events and prefabs
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..json_utils import safe_json_dump, safe_json_dumps


class EventTrigger(Enum):
    """Types of event triggers"""
    PLAYER_TOUCH = "player_touch"      # When player touches the event
    PLAYER_INTERACT = "player_interact"  # When player presses action key
    AUTO_RUN = "auto_run"              # Runs automatically when conditions are met
    PARALLEL = "parallel"              # Runs continuously in parallel
    ON_ENTER = "on_enter"              # When player enters the map
    ON_EXIT = "on_exit"                # When player exits the map
    TIMER = "timer"                    # Triggered by timer
    CUSTOM = "custom"                  # Custom trigger condition


class EventCondition(Enum):
    """Types of event conditions"""
    NONE = "none"                      # No condition
    SWITCH = "switch"                  # Game switch is on/off
    VARIABLE = "variable"              # Variable comparison
    ITEM = "item"                      # Player has item
    SCRIPT = "script"                  # Custom script condition


@dataclass
class LevelEvent:
    """Represents an event in a level"""
    id: str
    name: str
    position: Tuple[int, int]  # Grid position
    size: Tuple[int, int] = (1, 1)  # Size in grid cells
    
    # Trigger settings
    trigger: EventTrigger = EventTrigger.PLAYER_INTERACT
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    
    # Condition settings
    condition: EventCondition = EventCondition.NONE
    condition_data: Dict[str, Any] = field(default_factory=dict)
    
    # Visual settings
    sprite_texture: str = ""
    sprite_frame: int = 0
    direction: str = "down"  # "up", "down", "left", "right"
    visible: bool = True
    through: bool = False  # Can player walk through this event
    
    # Script/Prefab settings
    prefab_id: Optional[str] = None  # If this event uses a prefab
    prefab_overrides: Dict[str, Any] = field(default_factory=dict)
    visual_script: Dict[str, Any] = field(default_factory=dict)
    visual_script_path: Optional[str] = None  # Path to visual script file
    raw_script: str = ""
    
    # Metadata
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "position": list(self.position),
            "size": list(self.size),
            "trigger": self.trigger.value,
            "trigger_data": self.trigger_data,
            "condition": self.condition.value,
            "condition_data": self.condition_data,
            "sprite_texture": self.sprite_texture,
            "sprite_frame": self.sprite_frame,
            "direction": self.direction,
            "visible": self.visible,
            "through": self.through,
            "prefab_id": self.prefab_id,
            "prefab_overrides": self.prefab_overrides,
            "visual_script": self.visual_script,
            "visual_script_path": self.visual_script_path,
            "raw_script": self.raw_script,
            "notes": self.notes,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LevelEvent":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            position=tuple(data["position"]),
            size=tuple(data.get("size", [1, 1])),
            trigger=EventTrigger(data.get("trigger", "player_interact")),
            trigger_data=data.get("trigger_data", {}),
            condition=EventCondition(data.get("condition", "none")),
            condition_data=data.get("condition_data", {}),
            sprite_texture=data.get("sprite_texture", ""),
            sprite_frame=data.get("sprite_frame", 0),
            direction=data.get("direction", "down"),
            visible=data.get("visible", True),
            through=data.get("through", False),
            prefab_id=data.get("prefab_id"),
            prefab_overrides=data.get("prefab_overrides", {}),
            visual_script=data.get("visual_script", {}),
            visual_script_path=data.get("visual_script_path"),
            raw_script=data.get("raw_script", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", [])
        )


@dataclass
class LevelLayer:
    """Represents a layer in a level"""
    id: str
    name: str
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0
    blend_mode: str = "normal"
    
    # Layer content
    events: List[LevelEvent] = field(default_factory=list)
    tilemap_data: Optional[Dict[str, Any]] = None  # Optional tilemap background
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "visible": self.visible,
            "locked": self.locked,
            "opacity": self.opacity,
            "blend_mode": self.blend_mode,
            "events": [event.to_dict() for event in self.events],
            "tilemap_data": self.tilemap_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LevelLayer":
        """Create from dictionary"""
        layer = cls(
            id=data["id"],
            name=data["name"],
            visible=data.get("visible", True),
            locked=data.get("locked", False),
            opacity=data.get("opacity", 1.0),
            blend_mode=data.get("blend_mode", "normal"),
            tilemap_data=data.get("tilemap_data")
        )
        
        # Load events
        for event_data in data.get("events", []):
            event = LevelEvent.from_dict(event_data)
            layer.events.append(event)
        
        return layer


class Level:
    """Represents a complete level/map"""
    
    def __init__(self, name: str, width: int = 20, height: int = 15):
        self.id = str(uuid.uuid4())
        self.name = name
        self.width = width  # Width in grid cells
        self.height = height  # Height in grid cells
        self.cell_size = 32  # Size of each grid cell in pixels
        
        # Level properties
        self.description = ""
        self.background_color = "#2b2b2b"
        self.background_image = ""
        self.background_music = ""
        self.ambient_sound = ""
        
        # Grid settings
        self.show_grid = True
        self.snap_to_grid = True
        self.grid_color = "#404040"
        
        # Layers
        self.layers: List[LevelLayer] = []
        self.active_layer_id: Optional[str] = None
        
        # Global level events
        self.level_events: Dict[str, Any] = {}  # on_enter, on_exit, etc.
        
        # Metadata
        self.tags: List[str] = []
        self.version = "1.0.0"
        self.author = ""
        self.created_at = ""
        self.modified_at = ""
        
        # Create default layer
        self.create_default_layer()
    
    def create_default_layer(self):
        """Create the default layer"""
        default_layer = LevelLayer(
            id=str(uuid.uuid4()),
            name="Events"
        )
        self.layers.append(default_layer)
        self.active_layer_id = default_layer.id
    
    def add_layer(self, name: str) -> LevelLayer:
        """Add a new layer"""
        layer = LevelLayer(
            id=str(uuid.uuid4()),
            name=name
        )
        self.layers.append(layer)
        return layer
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer"""
        layer = self.get_layer_by_id(layer_id)
        if layer and len(self.layers) > 1:  # Don't remove the last layer
            self.layers.remove(layer)
            if self.active_layer_id == layer_id:
                self.active_layer_id = self.layers[0].id if self.layers else None
            return True
        return False
    
    def get_layer_by_id(self, layer_id: str) -> Optional[LevelLayer]:
        """Get layer by ID"""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None
    
    def get_active_layer(self) -> Optional[LevelLayer]:
        """Get the active layer"""
        if self.active_layer_id:
            return self.get_layer_by_id(self.active_layer_id)
        return self.layers[0] if self.layers else None
    
    def add_event(self, event: LevelEvent, layer_id: Optional[str] = None) -> bool:
        """Add an event to a layer"""
        target_layer = self.get_layer_by_id(layer_id) if layer_id else self.get_active_layer()
        if target_layer:
            target_layer.events.append(event)
            return True
        return False
    
    def remove_event(self, event_id: str) -> bool:
        """Remove an event from all layers"""
        for layer in self.layers:
            layer.events = [e for e in layer.events if e.id != event_id]
        return True
    
    def get_event_by_id(self, event_id: str) -> Optional[LevelEvent]:
        """Get event by ID"""
        for layer in self.layers:
            for event in layer.events:
                if event.id == event_id:
                    return event
        return None
    
    def get_events_at_position(self, x: int, y: int) -> List[LevelEvent]:
        """Get all events at a grid position"""
        events = []
        for layer in self.layers:
            if not layer.visible:
                continue
            for event in layer.events:
                ex, ey = event.position
                ew, eh = event.size
                if ex <= x < ex + ew and ey <= y < ey + eh:
                    events.append(event)
        return events
    
    def is_position_free(self, x: int, y: int, exclude_event_id: Optional[str] = None) -> bool:
        """Check if a position is free of non-through events"""
        for layer in self.layers:
            for event in layer.events:
                if exclude_event_id and event.id == exclude_event_id:
                    continue
                if not event.through:
                    ex, ey = event.position
                    ew, eh = event.size
                    if ex <= x < ex + ew and ey <= y < ey + eh:
                        return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "description": self.description,
            "background_color": self.background_color,
            "background_image": self.background_image,
            "background_music": self.background_music,
            "ambient_sound": self.ambient_sound,
            "show_grid": self.show_grid,
            "snap_to_grid": self.snap_to_grid,
            "grid_color": self.grid_color,
            "layers": [layer.to_dict() for layer in self.layers],
            "active_layer_id": self.active_layer_id,
            "level_events": self.level_events,
            "tags": self.tags,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at,
            "modified_at": self.modified_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Level":
        """Create from dictionary"""
        level = cls(
            name=data["name"],
            width=data.get("width", 20),
            height=data.get("height", 15)
        )
        
        level.id = data.get("id", str(uuid.uuid4()))
        level.cell_size = data.get("cell_size", 32)
        level.description = data.get("description", "")
        level.background_color = data.get("background_color", "#2b2b2b")
        level.background_image = data.get("background_image", "")
        level.background_music = data.get("background_music", "")
        level.ambient_sound = data.get("ambient_sound", "")
        level.show_grid = data.get("show_grid", True)
        level.snap_to_grid = data.get("snap_to_grid", True)
        level.grid_color = data.get("grid_color", "#404040")
        level.active_layer_id = data.get("active_layer_id")
        level.level_events = data.get("level_events", {})
        level.tags = data.get("tags", [])
        level.version = data.get("version", "1.0.0")
        level.author = data.get("author", "")
        level.created_at = data.get("created_at", "")
        level.modified_at = data.get("modified_at", "")
        
        # Clear default layer and load layers from data
        level.layers.clear()
        for layer_data in data.get("layers", []):
            layer = LevelLayer.from_dict(layer_data)
            level.layers.append(layer)
        
        # Ensure we have at least one layer
        if not level.layers:
            level.create_default_layer()
        
        return level
    
    def save_to_file(self, file_path: str):
        """Save level to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            safe_json_dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "Level":
        """Load level from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def export_to_scene(self, scene_path: str):
        """Export level to standard scene format"""
        scene_data = {
            "name": self.name,
            "nodes": []
        }

        # Create root node
        root_node = {
            "name": self.name,
            "type": "Node2D",
            "position": [0, 0],
            "children": []
        }

        # Add level background if any
        if self.background_image:
            bg_node = {
                "name": "Background",
                "type": "Sprite2D",
                "position": [0, 0],
                "texture": self.background_image,
                "children": []
            }
            root_node["children"].append(bg_node)

        # Convert events to scene nodes
        for layer in self.layers:
            if not layer.visible:
                continue

            # Create layer node
            layer_node = {
                "name": f"Layer_{layer.name}",
                "type": "Node2D",
                "position": [0, 0],
                "children": []
            }

            # Add events as child nodes
            for event in layer.events:
                event_node = {
                    "name": event.name,
                    "type": "Area2D",  # Most events are interactive areas
                    "position": [
                        event.position[0] * self.cell_size,
                        event.position[1] * self.cell_size
                    ],
                    "children": []
                }

                # Add collision shape
                collision_node = {
                    "name": "CollisionShape2D",
                    "type": "CollisionShape2D",
                    "position": [0, 0],
                    "shape": "rectangle",
                    "size": [
                        event.size[0] * self.cell_size,
                        event.size[1] * self.cell_size
                    ],
                    "children": []
                }
                event_node["children"].append(collision_node)

                # Add sprite if specified
                if event.sprite_texture:
                    sprite_node = {
                        "name": "Sprite",
                        "type": "Sprite2D",
                        "position": [0, 0],
                        "texture": event.sprite_texture,
                        "children": []
                    }
                    event_node["children"].append(sprite_node)

                # Add script if any
                if event.raw_script:
                    # Convert event script to node script format
                    node_script = f'''# Event: {event.name}
# Trigger: {event.trigger.value}

{event.raw_script}

# Event trigger handling
def _ready():
    if hasattr(self, 'body_entered'):
        body_entered.connect(_on_body_entered)

def _on_body_entered(body):
    if body.name == "Player":
        if hasattr(self, 'on_interact'):
            on_interact(body)
'''

                    # Save script to file
                    script_filename = f"{event.name}_{event.id[:8]}.py"
                    event_node["script"] = f"scripts/{script_filename}"

                    # Save the actual script file
                    script_path = Path(scene_path).parent.parent / "scripts" / script_filename
                    script_path.parent.mkdir(exist_ok=True)
                    with open(script_path, 'w', encoding='utf-8') as f:
                        f.write(node_script)

                # Add event metadata
                event_node["event_data"] = {
                    "trigger": event.trigger.value,
                    "through": event.through,
                    "visible": event.visible,
                    "notes": event.notes,
                    "tags": event.tags
                }

                layer_node["children"].append(event_node)

            if layer_node["children"]:  # Only add layer if it has events
                root_node["children"].append(layer_node)

        scene_data["nodes"].append(root_node)

        # Save scene file
        with open(scene_path, 'w', encoding='utf-8') as f:
            safe_json_dump(scene_data, f, indent=2)
