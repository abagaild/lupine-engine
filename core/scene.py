"""
Scene Management System for Lupine Engine
Handles scene loading, saving, and node management
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.project import LupineProject


class Node:
    """Base node class for scene hierarchy"""
    
    def __init__(self, name: str = "Node", node_type: str = "Node"):
        self.name = name
        self.type = node_type
        self.parent = None
        self.children = []
        self.properties = {}
        self.script_path = None
        
        # Common properties
        self.visible = True
        self.process_mode = "inherit"
    
    def add_child(self, child: 'Node'):
        """Add a child node"""
        if child.parent:
            child.parent.remove_child(child)
        
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'Node'):
        """Remove a child node"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def get_child(self, name: str) -> Optional['Node']:
        """Get child by name"""
        for child in self.children:
            if child.name == name:
                return child
        return None
    
    def find_node(self, path: str) -> Optional['Node']:
        """Find node by path (e.g., "Child/Grandchild")"""
        if not path:
            return self
        
        parts = path.split('/', 1)
        child_name = parts[0]
        remaining_path = parts[1] if len(parts) > 1 else ""
        
        child = self.get_child(child_name)
        if child:
            return child.find_node(remaining_path)
        
        return None
    
    def get_path(self) -> str:
        """Get path from root to this node"""
        if not self.parent:
            return self.name
        return f"{self.parent.get_path()}/{self.name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization"""
        data = {
            "name": self.name,
            "type": self.type,
            "visible": self.visible,
            "process_mode": self.process_mode,
            "properties": self.properties.copy(),
            "children": [child.to_dict() for child in self.children]
        }
        
        if self.script_path:
            data["script"] = self.script_path
        
        return data

    @classmethod
    def _apply_node_properties(cls, node: 'Node', data: Dict[str, Any]):
        """Apply properties from data dictionary to node"""
        import copy

        # Set common properties
        node.visible = data.get("visible", True)
        node.process_mode = data.get("process_mode", "inherit")

        # Ensure each node gets its own properties dictionary
        node.properties = copy.deepcopy(data.get("properties", {}))

        # Set script path if available
        script_path = data.get("script_path") or data.get("script")
        if script_path:
            node.script_path = str(script_path)

        # Apply type-specific properties based on node type
        node_type = data.get("type", "Node")

        # Node2D properties - ensure each instance gets its own copy
        if hasattr(node, 'position') and isinstance(getattr(node, 'position', None), list):
            node.position = copy.deepcopy(data.get("position", [0.0, 0.0]))
            node.rotation = data.get("rotation", 0.0)
            node.scale = copy.deepcopy(data.get("scale", [1.0, 1.0]))
            if hasattr(node, 'z_index'):
                node.z_index = data.get("z_index", 0)
                node.z_as_relative = data.get("z_as_relative", True)

        # Apply all other properties dynamically - ensure unique instances
        for key, value in data.items():
            if key not in ["name", "type", "visible", "process_mode", "properties", "script", "script_path", "children", "position", "rotation", "scale", "z_index", "z_as_relative"]:
                if hasattr(node, key):
                    try:
                        # For mutable types, create deep copies to ensure uniqueness
                        if isinstance(value, (list, dict)):
                            setattr(node, key, copy.deepcopy(value))
                        else:
                            setattr(node, key, value)
                    except Exception as e:
                        print(f"Warning: Could not set property {key} on {node_type}: {e}")
                else:
                    # Store as custom property with deep copy for mutable types
                    if isinstance(value, (list, dict)):
                        node.properties[key] = copy.deepcopy(value)
                    else:
                        node.properties[key] = value

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary"""
        node_type = data.get("type", "Node")

        # Try to use node registry for dynamic node creation
        try:
            from core.node_registry import get_node_registry
            registry = get_node_registry()
            node_def = registry.get_node_definition(node_type)
            if node_def:
                # Create node using registry
                node = registry.create_node_instance(node_type, data.get("name"))
                # Apply all properties from data
                cls._apply_node_properties(node, data)

                # Add children recursively
                for child_data in data.get("children", []):
                    child = Node.from_dict(child_data)
                    node.add_child(child)

                return node
        except Exception as e:
            print(f"Warning: Could not create node {node_type} using registry: {e}")

        # Fallback to hardcoded node creation
        if node_type == "Node2D":
            node = Node2D(data.get("name", "Node2D"))
        elif node_type == "Sprite":
            node = Sprite(data.get("name", "Sprite"))
            # Set Sprite-specific properties
            node.texture = data.get("texture", None)
            node.normal_map = data.get("normal_map", None)
            node.centered = data.get("centered", True)
            node.offset = data.get("offset", [0.0, 0.0])
            node.flip_h = data.get("flip_h", False)
            node.flip_v = data.get("flip_v", False)
            node.region_enabled = data.get("region_enabled", False)
            node.region_rect = data.get("region_rect", [0, 0, 0, 0])
            node.region_filter_clip = data.get("region_filter_clip", False)
            node.hframes = data.get("hframes", 1)
            node.vframes = data.get("vframes", 1)
            node.frame = data.get("frame", 0)
        elif node_type == "AnimatedSprite":
            node = AnimatedSprite(data.get("name", "AnimatedSprite"))
            # Set AnimatedSprite-specific properties
            node.sprite_frames = data.get("sprite_frames", None)
            node.animation = data.get("animation", "default")
            node.frame = data.get("frame", 0)
            node.speed_scale = data.get("speed_scale", 1.0)
            node.playing = data.get("playing", False)
            node.autoplay = data.get("autoplay", "")
            node.frame_progress = data.get("frame_progress", 0.0)
            # Inherit Sprite properties
            node.texture = data.get("texture", None)
            node.normal_map = data.get("normal_map", None)
            node.centered = data.get("centered", True)
            node.offset = data.get("offset", [0.0, 0.0])
            node.flip_h = data.get("flip_h", False)
            node.flip_v = data.get("flip_v", False)
            node.region_enabled = data.get("region_enabled", False)
            node.region_rect = data.get("region_rect", [0, 0, 0, 0])
            node.region_filter_clip = data.get("region_filter_clip", False)
            node.hframes = data.get("hframes", 1)
            node.vframes = data.get("vframes", 1)
            node.frame_coords = data.get("frame_coords", [0, 0])
            node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
            node.self_modulate = data.get("self_modulate", [1.0, 1.0, 1.0, 1.0])
        elif node_type == "Timer":
            node = Timer(data.get("name", "Timer"))
            # Set Timer-specific properties
            node.wait_time = data.get("wait_time", 1.0)
            node.one_shot = data.get("one_shot", True)
            node.autostart = data.get("autostart", False)
            node.paused = data.get("paused", False)
            node._time_left = data.get("_time_left", 0.0)
            node._is_running = data.get("_is_running", False)
        elif node_type == "Camera2D":
            node = Camera2D(data.get("name", "Camera2D"))
            # Set Camera2D-specific properties
            node.current = data.get("current", False)
            node.enabled = data.get("enabled", True)
            node.offset = data.get("offset", [0.0, 0.0])
            node.zoom = data.get("zoom", [1.0, 1.0])
            node.anchor_mode = data.get("anchor_mode", "fixed_top_left")
            node.drag_margin_h_enabled = data.get("drag_margin_h_enabled", False)
            node.drag_margin_v_enabled = data.get("drag_margin_v_enabled", False)
            node.drag_margin_left = data.get("drag_margin_left", 0.2)
            node.drag_margin_top = data.get("drag_margin_top", 0.2)
            node.drag_margin_right = data.get("drag_margin_right", 0.2)
            node.drag_margin_bottom = data.get("drag_margin_bottom", 0.2)
            node.limit_left = data.get("limit_left", -10000000)
            node.limit_top = data.get("limit_top", -10000000)
            node.limit_right = data.get("limit_right", 10000000)
            node.limit_bottom = data.get("limit_bottom", 10000000)
            node.limit_smoothed = data.get("limit_smoothed", False)
            node.smoothing_enabled = data.get("smoothing_enabled", False)
            node.smoothing_speed = data.get("smoothing_speed", 5.0)
            node.follow_target = data.get("follow_target", None)
            node.follow_smoothing = data.get("follow_smoothing", True)
            node.shake_intensity = data.get("shake_intensity", 0.0)
            node.shake_duration = data.get("shake_duration", 0.0)
            node.shake_timer = data.get("shake_timer", 0.0)
            node.process_mode = data.get("process_mode", "idle")
        elif node_type == "Area2D":
            node = Area2D(data.get("name", "Area2D"))
        elif node_type == "KinematicBody2D":
            node = KinematicBody2D(data.get("name", "KinematicBody2D"))
            # Set KinematicBody2D-specific properties
            node.collision_layer = data.get("collision_layer", 1)
            node.collision_mask = data.get("collision_mask", 1)
            node.safe_margin = data.get("safe_margin", 0.08)
            node.motion_sync_to_physics = data.get("motion_sync_to_physics", False)
        elif node_type == "Control":
            node = Control(data.get("name", "Control"))
            # Set Control-specific properties - using 'position' instead of 'rect_position' per user preference
            node.position = data.get("position", data.get("rect_position", [0.0, 0.0]))  # Support both for compatibility
            node.rect_size = data.get("rect_size", [100.0, 100.0])
            node.rect_min_size = data.get("rect_min_size", [0.0, 0.0])
            node.anchor_left = data.get("anchor_left", 0.0)
            node.anchor_top = data.get("anchor_top", 0.0)
            node.anchor_right = data.get("anchor_right", 0.0)
            node.anchor_bottom = data.get("anchor_bottom", 0.0)
            node.margin_left = data.get("margin_left", 0.0)
            node.margin_top = data.get("margin_top", 0.0)
            node.margin_right = data.get("margin_right", 0.0)
            node.margin_bottom = data.get("margin_bottom", 0.0)
            node.size_flags = data.get("size_flags", {"expand_h": False, "expand_v": False})
            node.clip_contents = data.get("clip_contents", False)
            node.mouse_filter = data.get("mouse_filter", "pass")
            node.focus_mode = data.get("focus_mode", "none")
            node.theme = data.get("theme", None)
            node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
            node.z_layer = data.get("z_layer", 0)
        elif node_type == "Panel":
            node = Panel(data.get("name", "Panel"))
            # Set Control properties first (Panel inherits from Control)
            node.position = data.get("position", data.get("rect_position", [0.0, 0.0]))  # Support both for compatibility
            node.rect_size = data.get("rect_size", [100.0, 100.0])
            node.rect_min_size = data.get("rect_min_size", [0.0, 0.0])
            node.anchor_left = data.get("anchor_left", 0.0)
            node.anchor_top = data.get("anchor_top", 0.0)
            node.anchor_right = data.get("anchor_right", 0.0)
            node.anchor_bottom = data.get("anchor_bottom", 0.0)
            node.margin_left = data.get("margin_left", 0.0)
            node.margin_top = data.get("margin_top", 0.0)
            node.margin_right = data.get("margin_right", 0.0)
            node.margin_bottom = data.get("margin_bottom", 0.0)
            node.size_flags = data.get("size_flags", {"expand_h": False, "expand_v": False})
            node.clip_contents = data.get("clip_contents", False)
            node.mouse_filter = data.get("mouse_filter", "pass")
            node.focus_mode = data.get("focus_mode", "none")
            node.theme = data.get("theme", None)
            node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
            node.z_layer = data.get("z_layer", 0)
            # Set Panel-specific properties
            node.panel_color = data.get("panel_color", [0.2, 0.2, 0.2, 1.0])
            node.corner_radius = data.get("corner_radius", 0.0)
            node.border_width = data.get("border_width", 0.0)
            node.border_color = data.get("border_color", [0.0, 0.0, 0.0, 1.0])
            node.texture = data.get("texture", None)
        elif node_type == "Label":
            node = Label(data.get("name", "Label"))
            # Set Control properties first (Label inherits from Control)
            node.position = data.get("position", data.get("rect_position", [0.0, 0.0]))  # Support both for compatibility
            node.rect_size = data.get("rect_size", [100.0, 50.0])
            node.rect_min_size = data.get("rect_min_size", [0.0, 0.0])
            node.anchor_left = data.get("anchor_left", 0.0)
            node.anchor_top = data.get("anchor_top", 0.0)
            node.anchor_right = data.get("anchor_right", 0.0)
            node.anchor_bottom = data.get("anchor_bottom", 0.0)
            node.margin_left = data.get("margin_left", 0.0)
            node.margin_top = data.get("margin_top", 0.0)
            node.margin_right = data.get("margin_right", 0.0)
            node.margin_bottom = data.get("margin_bottom", 0.0)
            node.size_flags = data.get("size_flags", {"expand_h": False, "expand_v": False})
            node.clip_contents = data.get("clip_contents", False)
            node.mouse_filter = data.get("mouse_filter", "pass")
            node.focus_mode = data.get("focus_mode", "none")
            node.theme = data.get("theme", None)
            node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
            node.z_layer = data.get("z_layer", 0)
            # Set Label-specific properties
            node.text = data.get("text", "Label")
            node.autowrap = data.get("autowrap", False)
            node.clip_text = data.get("clip_text", False)
            node.font = data.get("font", None)
            node.font_size = data.get("font_size", 14)
            node.font_style = data.get("font_style", "Regular")
            node.font_color = data.get("font_color", [1.0, 1.0, 1.0, 1.0])
            node.outline_color = data.get("outline_color", [0.0, 0.0, 0.0, 1.0])
            node.outline_size = data.get("outline_size", 0.0)
            node.h_align = data.get("h_align", "Left")
            node.v_align = data.get("v_align", "Top")
        elif node_type == "Button":
            node = Button(data.get("name", "Button"))
            # Set Control properties first (Button inherits from Control)
            node.position = data.get("position", data.get("rect_position", [0.0, 0.0]))  # Support both for compatibility
            node.rect_size = data.get("rect_size", [100.0, 30.0])
            node.rect_min_size = data.get("rect_min_size", [0.0, 0.0])
            node.anchor_left = data.get("anchor_left", 0.0)
            node.anchor_top = data.get("anchor_top", 0.0)
            node.anchor_right = data.get("anchor_right", 0.0)
            node.anchor_bottom = data.get("anchor_bottom", 0.0)
            node.margin_left = data.get("margin_left", 0.0)
            node.margin_top = data.get("margin_top", 0.0)
            node.margin_right = data.get("margin_right", 0.0)
            node.margin_bottom = data.get("margin_bottom", 0.0)
            node.size_flags = data.get("size_flags", {"expand_h": False, "expand_v": False})
            node.clip_contents = data.get("clip_contents", False)
            node.mouse_filter = data.get("mouse_filter", "pass")
            node.focus_mode = data.get("focus_mode", "none")
            node.theme = data.get("theme", None)
            node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
            node.z_layer = data.get("z_layer", 0)
            # Set Button-specific properties
            node.text = data.get("text", "Button")
            node.font = data.get("font", None)
            node.font_size = data.get("font_size", 14)
            node.font_style = data.get("font_style", "Regular")
            node.normal_color = data.get("normal_color", [0.3, 0.3, 0.3, 1.0])
            node.hover_color = data.get("hover_color", [0.4, 0.4, 0.4, 1.0])
            node.pressed_color = data.get("pressed_color", [0.2, 0.2, 0.2, 1.0])
            node.disabled_color = data.get("disabled_color", [0.15, 0.15, 0.15, 1.0])
            node.font_color = data.get("font_color", [1.0, 1.0, 1.0, 1.0])
            node.corner_radius = data.get("corner_radius", 4.0)
            node.border_width = data.get("border_width", 1.0)
            node.border_color = data.get("border_color", [0.5, 0.5, 0.5, 1.0])
            node.disabled = data.get("disabled", False)
            node.toggle_mode = data.get("toggle_mode", False)
            node.pressed = data.get("pressed", False)
            node._is_hovered = data.get("_is_hovered", False)
            node._is_mouse_pressed = data.get("_is_mouse_pressed", False)
        elif node_type == "CanvasLayer":
            node = CanvasLayer(data.get("name", "CanvasLayer"))
            # Set CanvasLayer-specific properties
            node.layer = data.get("layer", 1)
            node.offset = data.get("offset", [0.0, 0.0])
            node.rotation = data.get("rotation", 0.0)
            node.scale = data.get("scale", [1.0, 1.0])
            node.follow_viewport_enable = data.get("follow_viewport_enable", False)
            node.follow_viewport_scale = data.get("follow_viewport_scale", 1.0)
            node.custom_viewport = data.get("custom_viewport", None)
        else:
            node = Node(data.get("name", "Node"), node_type)
        
        # Set properties
        node.visible = data.get("visible", True)
        node.process_mode = data.get("process_mode", "inherit")
        node.properties = data.get("properties", {})
        node.script_path = data.get("script") or ""

        # Set Node2D properties for Node2D-derived classes
        if isinstance(node, Node2D):
            node.position = data.get("position", [0.0, 0.0])
            node.rotation = data.get("rotation", 0.0)
            node.scale = data.get("scale", [1.0, 1.0])
            node.z_index = data.get("z_index", 0)
            node.z_as_relative = data.get("z_as_relative", True)
        
        # Add children
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        
        return node


class Node2D(Node):
    """2D node with transform properties"""
    
    def __init__(self, name: str = "Node2D"):
        super().__init__(name, "Node2D")
        self.position = [0.0, 0.0]
        self.rotation = 0.0
        self.scale = [1.0, 1.0]
        self.z_index = 0
        self.z_as_relative = True
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "z_index": self.z_index,
            "z_as_relative": self.z_as_relative
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node2D':
        node = cls(data.get("name", "Node2D"))
        node.position = data.get("position", [0.0, 0.0])
        node.rotation = data.get("rotation", 0.0)
        node.scale = data.get("scale", [1.0, 1.0])
        node.z_index = data.get("z_index", 0)
        node.z_as_relative = data.get("z_as_relative", True)
        return node


class Sprite(Node2D):
    """Sprite node for displaying textures - equivalent to Godot's Sprite2D"""

    def __init__(self, name: str = "Sprite"):
        super().__init__(name)
        self.type = "Sprite"

        # Texture properties
        self.texture = None
        self.normal_map = None

        # Transform properties
        self.centered = True
        self.offset = [0.0, 0.0]
        self.flip_h = False
        self.flip_v = False

        # Region properties
        self.region_enabled = False
        self.region_rect = [0, 0, 0, 0]  # x, y, width, height
        self.region_filter_clip = False

        # Animation properties
        self.hframes = 1
        self.vframes = 1
        self.frame = 0
        self.frame_coords = [0, 0]

        # Rendering properties
        self.modulate = [1.0, 1.0, 1.0, 1.0]  # RGBA
        self.self_modulate = [1.0, 1.0, 1.0, 1.0]  # RGBA

        # Set default script
        self.script_path = "nodes/Sprite.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            # Texture properties
            "texture": self.texture,
            "normal_map": self.normal_map,

            # Transform properties
            "centered": self.centered,
            "offset": self.offset,
            "flip_h": self.flip_h,
            "flip_v": self.flip_v,

            # Region properties
            "region_enabled": self.region_enabled,
            "region_rect": self.region_rect,
            "region_filter_clip": self.region_filter_clip,

            # Animation properties
            "hframes": self.hframes,
            "vframes": self.vframes,
            "frame": self.frame,
            "frame_coords": self.frame_coords,

            # Rendering properties
            "modulate": self.modulate,
            "self_modulate": self.self_modulate
        })
        return data


class AnimatedSprite(Sprite):
    """AnimatedSprite node for displaying animated textures - equivalent to Godot's AnimatedSprite2D"""

    def __init__(self, name: str = "AnimatedSprite"):
        super().__init__(name)
        self.type = "AnimatedSprite"

        # Animation properties
        self.sprite_frames = None  # SpriteFrames resource
        self.animation = "default"  # Current animation name
        self.speed_scale = 1.0  # Animation speed multiplier
        self.playing = False  # Whether animation is playing
        self.autoplay = ""  # Animation to autoplay on ready
        self.frame_progress = 0.0  # Progress within current frame

        # Set default script
        self.script_path = "nodes/AnimatedSprite.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "sprite_frames": self.sprite_frames,
            "animation": self.animation,
            "speed_scale": self.speed_scale,
            "playing": self.playing,
            "autoplay": self.autoplay,
            "frame_progress": self.frame_progress
        })
        return data


class Timer(Node):
    """Timer node for delays, cooldowns, and scheduled events"""

    def __init__(self, name: str = "Timer"):
        super().__init__(name)
        self.type = "Timer"

        # Timing properties
        self.wait_time = 1.0  # seconds until timeout
        self.one_shot = True  # if true, fires only once; otherwise repeats
        self.autostart = False  # if true, starts counting as soon as the node enters tree
        self.paused = False  # freeze the timer until un-paused

        # Internal state (read-only)
        self._time_left = 0.0  # seconds remaining until next timeout
        self._is_running = False  # whether timer is currently active

        # Set default script
        self.script_path = "nodes/Timer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "wait_time": self.wait_time,
            "one_shot": self.one_shot,
            "autostart": self.autostart,
            "paused": self.paused,
            "_time_left": self._time_left,
            "_is_running": self._is_running
        })
        return data


class Camera2D(Node2D):
    """2D camera node - Enhanced Godot-like implementation"""

    def __init__(self, name: str = "Camera2D"):
        super().__init__(name)
        self.type = "Camera2D"

        # Camera state
        self.current = False
        self.enabled = True

        # Transform properties
        self.offset = [0.0, 0.0]  # Camera offset from position
        self.zoom = [1.0, 1.0]  # Camera zoom (1.0 = normal, 2.0 = 2x zoom)

        # Anchor and drag properties
        self.anchor_mode = "fixed_top_left"  # "fixed_top_left", "drag_center"
        self.drag_margin_h_enabled = False
        self.drag_margin_v_enabled = False
        self.drag_margin_left = 0.2
        self.drag_margin_top = 0.2
        self.drag_margin_right = 0.2
        self.drag_margin_bottom = 0.2

        # Limit properties
        self.limit_left = -10000000
        self.limit_top = -10000000
        self.limit_right = 10000000
        self.limit_bottom = 10000000
        self.limit_smoothed = False

        # Smoothing properties
        self.smoothing_enabled = False
        self.smoothing_speed = 5.0

        # Following properties
        self.follow_target = None  # Node to follow
        self.follow_smoothing = True

        # Camera shake
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_timer = 0.0

        # Process mode
        self.process_mode = "idle"  # "idle", "physics", "always"

        # Set default script
        self.script_path = "nodes/Camera2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            # Camera state
            "current": self.current,
            "enabled": self.enabled,

            # Transform properties
            "offset": self.offset,
            "zoom": self.zoom,

            # Anchor and drag properties
            "anchor_mode": self.anchor_mode,
            "drag_margin_h_enabled": self.drag_margin_h_enabled,
            "drag_margin_v_enabled": self.drag_margin_v_enabled,
            "drag_margin_left": self.drag_margin_left,
            "drag_margin_top": self.drag_margin_top,
            "drag_margin_right": self.drag_margin_right,
            "drag_margin_bottom": self.drag_margin_bottom,

            # Limit properties
            "limit_left": self.limit_left,
            "limit_top": self.limit_top,
            "limit_right": self.limit_right,
            "limit_bottom": self.limit_bottom,
            "limit_smoothed": self.limit_smoothed,

            # Smoothing properties
            "smoothing_enabled": self.smoothing_enabled,
            "smoothing_speed": self.smoothing_speed,

            # Following properties
            "follow_target": self.follow_target,
            "follow_smoothing": self.follow_smoothing,

            # Camera shake
            "shake_intensity": self.shake_intensity,
            "shake_duration": self.shake_duration,
            "shake_timer": self.shake_timer,

            # Process mode
            "process_mode": self.process_mode
        })
        return data


class CollisionShape2D(Node2D):
    """2D collision shape for physics bodies"""

    def __init__(self, name: str = "CollisionShape2D"):
        super().__init__(name)
        self.type = "CollisionShape2D"

        # Shape properties
        self.shape = "rectangle"  # "rectangle", "circle", "capsule", "segment"
        self.disabled = False
        self.one_way_collision = False
        self.one_way_collision_margin = 1.0

        # Shape-specific properties
        self.size = [32.0, 32.0]  # For rectangle
        self.radius = 16.0  # For circle/capsule
        self.height = 32.0  # For capsule
        self.point_a = [0.0, 0.0]  # For segment
        self.point_b = [32.0, 0.0]  # For segment

        # Debug properties
        self.debug_color = [0.0, 0.6, 0.7, 0.5]  # RGBA

        # Set default script
        self.script_path = "nodes/node2d/CollisionShape2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "shape": self.shape,
            "disabled": self.disabled,
            "one_way_collision": self.one_way_collision,
            "one_way_collision_margin": self.one_way_collision_margin,
            "size": self.size,
            "radius": self.radius,
            "height": self.height,
            "point_a": self.point_a,
            "point_b": self.point_b,
            "debug_color": self.debug_color
        })
        return data


class CollisionPolygon2D(Node2D):
    """2D polygon collision shape"""

    def __init__(self, name: str = "CollisionPolygon2D"):
        super().__init__(name)
        self.type = "CollisionPolygon2D"

        # Polygon properties
        self.polygon = [[0.0, 0.0], [32.0, 0.0], [32.0, 32.0], [0.0, 32.0]]  # Default square
        self.disabled = False
        self.one_way_collision = False
        self.one_way_collision_margin = 1.0

        # Build mode
        self.build_mode = "solids"  # "solids", "segments"

        # Debug properties
        self.debug_color = [0.0, 0.6, 0.7, 0.5]  # RGBA

        # Set default script
        self.script_path = "nodes/CollisionPolygon2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "polygon": self.polygon,
            "disabled": self.disabled,
            "one_way_collision": self.one_way_collision,
            "one_way_collision_margin": self.one_way_collision_margin,
            "build_mode": self.build_mode,
            "debug_color": self.debug_color
        })
        return data


class Area2D(Node2D):
    """2D area for collision detection"""

    def __init__(self, name: str = "Area2D"):
        super().__init__(name)
        self.type = "Area2D"

        # Detection properties
        self.monitoring = True
        self.monitorable = True

        # Collision properties
        self.collision_layer = 1
        self.collision_mask = 1

        # Physics properties
        self.gravity_space_override = "disabled"  # "disabled", "combine", "replace"
        self.gravity = [0.0, 98.0]
        self.gravity_point = [0.0, 0.0]
        self.gravity_distance_scale = 0.0
        self.gravity_vector = [0.0, 1.0]

        # Linear and angular damping
        self.linear_damp_space_override = "disabled"
        self.linear_damp = 0.1
        self.angular_damp_space_override = "disabled"
        self.angular_damp = 1.0

        # Audio properties
        self.audio_bus_override = False
        self.audio_bus_name = "Master"

        # Set default script
        self.script_path = "nodes/node2d/Area2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "monitoring": self.monitoring,
            "monitorable": self.monitorable,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "gravity_space_override": self.gravity_space_override,
            "gravity": self.gravity,
            "gravity_point": self.gravity_point,
            "gravity_distance_scale": self.gravity_distance_scale,
            "gravity_vector": self.gravity_vector,
            "linear_damp_space_override": self.linear_damp_space_override,
            "linear_damp": self.linear_damp,
            "angular_damp_space_override": self.angular_damp_space_override,
            "angular_damp": self.angular_damp,
            "audio_bus_override": self.audio_bus_override,
            "audio_bus_name": self.audio_bus_name
        })
        return data


class RigidBody2D(Node2D):
    """2D rigid body with physics simulation"""

    def __init__(self, name: str = "RigidBody2D"):
        super().__init__(name)
        self.type = "RigidBody2D"

        # Physics properties
        self.mode = "rigid"  # "rigid", "static", "character", "kinematic"
        self.mass = 1.0
        self.weight = 9.8  # mass * gravity
        self.physics_material_override = None

        # Damping
        self.linear_damp = -1.0  # -1 uses global default
        self.angular_damp = -1.0  # -1 uses global default

        # Collision
        self.collision_layer = 1
        self.collision_mask = 1

        # Motion
        self.gravity_scale = 1.0
        self.can_sleep = True
        self.sleeping = False
        self.lock_rotation = False

        # Continuous collision detection
        self.continuous_cd = "disabled"  # "disabled", "cast_ray", "cast_shape"
        self.contacts_reported = 0
        self.contact_monitor = False

        # Custom integrator
        self.custom_integrator = False

        # Set default script
        self.script_path = "nodes/RigidBody2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "mode": self.mode,
            "mass": self.mass,
            "weight": self.weight,
            "physics_material_override": self.physics_material_override,
            "linear_damp": self.linear_damp,
            "angular_damp": self.angular_damp,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "gravity_scale": self.gravity_scale,
            "can_sleep": self.can_sleep,
            "sleeping": self.sleeping,
            "lock_rotation": self.lock_rotation,
            "continuous_cd": self.continuous_cd,
            "contacts_reported": self.contacts_reported,
            "contact_monitor": self.contact_monitor,
            "custom_integrator": self.custom_integrator
        })
        return data


class StaticBody2D(Node2D):
    """2D static body for immovable objects"""

    def __init__(self, name: str = "StaticBody2D"):
        super().__init__(name)
        self.type = "StaticBody2D"

        # Physics properties
        self.physics_material_override = None

        # Collision properties
        self.collision_layer = 1
        self.collision_mask = 1

        # Constant motion (for moving platforms)
        self.constant_linear_velocity = [0.0, 0.0]
        self.constant_angular_velocity = 0.0

        # Set default script
        self.script_path = "nodes/StaticBody2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "physics_material_override": self.physics_material_override,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "constant_linear_velocity": self.constant_linear_velocity,
            "constant_angular_velocity": self.constant_angular_velocity
        })
        return data


class KinematicBody2D(Node2D):
    """2D kinematic body for manual movement with collision detection"""

    def __init__(self, name: str = "KinematicBody2D"):
        super().__init__(name)
        self.type = "KinematicBody2D"

        # Motion properties
        self.motion_sync_to_physics = False

        # Collision properties
        self.collision_layer = 1
        self.collision_mask = 1

        # Movement properties
        self.safe_margin = 0.08

        # Set default script
        self.script_path = "nodes/KinematicBody2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "motion_sync_to_physics": self.motion_sync_to_physics,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "safe_margin": self.safe_margin
        })
        return data


class Control(Node):
    """Base UI node with rect, layout, anchors, and margins"""

    def __init__(self, name: str = "Control"):
        super().__init__(name, "Control")

        # Rect properties - using 'position' instead of 'rect_position' per user preference
        self.position = [0.0, 0.0]  # Position relative to parent (UI coordinate system)
        self.rect_size = [100.0, 100.0]  # Size of the control
        self.rect_min_size = [0.0, 0.0]  # Minimum size

        # Anchor properties (0.0 to 1.0 relative to parent)
        self.anchor_left = 0.0
        self.anchor_top = 0.0
        self.anchor_right = 0.0
        self.anchor_bottom = 0.0

        # Margin properties (offset from anchors)
        self.margin_left = 0.0
        self.margin_top = 0.0
        self.margin_right = 0.0
        self.margin_bottom = 0.0

        # Layout properties
        self.size_flags = {"expand_h": False, "expand_v": False}

        # Visibility and focus
        self.clip_contents = False
        self.mouse_filter = "pass"  # "pass", "stop", "ignore"
        self.focus_mode = "none"  # "none", "click", "all"

        # Theme properties
        self.theme = None
        self.modulate = [1.0, 1.0, 1.0, 1.0]  # RGBA

        # Z-layer for UI ordering
        self.z_layer = 0

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            # Rect properties - using 'position' instead of 'rect_position' per user preference
            "position": self.position,
            "rect_size": self.rect_size,
            "rect_min_size": self.rect_min_size,

            # Anchor properties
            "anchor_left": self.anchor_left,
            "anchor_top": self.anchor_top,
            "anchor_right": self.anchor_right,
            "anchor_bottom": self.anchor_bottom,

            # Margin properties
            "margin_left": self.margin_left,
            "margin_top": self.margin_top,
            "margin_right": self.margin_right,
            "margin_bottom": self.margin_bottom,

            # Layout properties
            "size_flags": self.size_flags,

            # Other properties
            "clip_contents": self.clip_contents,
            "mouse_filter": self.mouse_filter,
            "focus_mode": self.focus_mode,
            "theme": self.theme,
            "modulate": self.modulate,
            "z_layer": self.z_layer
        })
        return data


class Panel(Control):
    """Simple rectangular container with background"""

    def __init__(self, name: str = "Panel"):
        super().__init__(name)
        self.type = "Panel"

        # Style properties
        self.panel_color = [0.2, 0.2, 0.2, 1.0]  # RGBA
        self.corner_radius = 0.0
        self.border_width = 0.0
        self.border_color = [0.0, 0.0, 0.0, 1.0]  # RGBA
        self.texture = None  # Optional background texture

        # Set default script
        self.script_path = "nodes/Panel.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "panel_color": self.panel_color,
            "corner_radius": self.corner_radius,
            "border_width": self.border_width,
            "border_color": self.border_color,
            "texture": self.texture
        })
        return data


class Label(Control):
    """UI node that displays text on screen"""

    def __init__(self, name: str = "Label"):
        super().__init__(name)
        self.type = "Label"

        # Text properties
        self.text = "Label"
        self.autowrap = False
        self.clip_text = False

        # Font properties
        self.font = None  # Font resource
        self.font_size = 14
        self.font_style = "Regular"  # "Regular", "Bold", "Italic"

        # Color and effects
        self.font_color = [1.0, 1.0, 1.0, 1.0]  # RGBA
        self.outline_color = [0.0, 0.0, 0.0, 1.0]  # RGBA
        self.outline_size = 0.0

        # Alignment
        self.h_align = "Left"  # "Left", "Center", "Right"
        self.v_align = "Top"  # "Top", "Center", "Bottom"

        # Set default script
        self.script_path = "nodes/Label.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            # Text properties
            "text": self.text,
            "autowrap": self.autowrap,
            "clip_text": self.clip_text,

            # Font properties
            "font": self.font,
            "font_size": self.font_size,
            "font_style": self.font_style,

            # Color and effects
            "font_color": self.font_color,
            "outline_color": self.outline_color,
            "outline_size": self.outline_size,

            # Alignment
            "h_align": self.h_align,
            "v_align": self.v_align
        })
        return data


class Button(Control):
    """Interactive button UI node with click, hover, and press states"""

    def __init__(self, name: str = "Button"):
        super().__init__(name)
        self.type = "Button"

        # Text properties
        self.text = "Button"
        self.font = None  # Font resource
        self.font_size = 14
        self.font_style = "Regular"  # "Regular", "Bold", "Italic"

        # Button state colors
        self.normal_color = [0.3, 0.3, 0.3, 1.0]  # RGBA - default button color
        self.hover_color = [0.4, 0.4, 0.4, 1.0]   # RGBA - color when hovered
        self.pressed_color = [0.2, 0.2, 0.2, 1.0] # RGBA - color when pressed
        self.disabled_color = [0.15, 0.15, 0.15, 1.0] # RGBA - color when disabled
        self.font_color = [1.0, 1.0, 1.0, 1.0]    # RGBA - text color

        # Style properties
        self.corner_radius = 4.0
        self.border_width = 1.0
        self.border_color = [0.5, 0.5, 0.5, 1.0]  # RGBA

        # Behavior properties
        self.disabled = False
        self.toggle_mode = False  # If true, button acts as toggle
        self.pressed = False      # Current pressed state (for toggle mode)

        # Internal state (not exported)
        self._is_hovered = False
        self._is_mouse_pressed = False

        # Set default size for buttons
        self.rect_size = [100.0, 30.0]

        # Set default script
        self.script_path = "nodes/Button.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            # Text properties
            "text": self.text,
            "font": self.font,
            "font_size": self.font_size,
            "font_style": self.font_style,

            # Button state colors
            "normal_color": self.normal_color,
            "hover_color": self.hover_color,
            "pressed_color": self.pressed_color,
            "disabled_color": self.disabled_color,
            "font_color": self.font_color,

            # Style properties
            "corner_radius": self.corner_radius,
            "border_width": self.border_width,
            "border_color": self.border_color,

            # Behavior properties
            "disabled": self.disabled,
            "toggle_mode": self.toggle_mode,
            "pressed": self.pressed,

            # Internal state
            "_is_hovered": getattr(self, '_is_hovered', False),
            "_is_mouse_pressed": getattr(self, '_is_mouse_pressed', False)
        })
        return data


class CanvasLayer(Node):
    """Canvas layer for UI and effects with independent rendering"""

    def __init__(self, name: str = "CanvasLayer"):
        super().__init__(name, "CanvasLayer")

        # Layer properties
        self.layer = 1  # Layer index for Z-ordering (higher = on top)

        # Transform properties
        self.offset = [0.0, 0.0]  # Layer offset
        self.rotation = 0.0  # Layer rotation in radians
        self.scale = [1.0, 1.0]  # Layer scale

        # Viewport properties
        self.follow_viewport_enable = False  # Follow viewport transformations
        self.follow_viewport_scale = 1.0  # Scale factor for viewport following

        # Custom viewport (if not following main viewport)
        self.custom_viewport = None

        # Set default script
        self.script_path = "nodes/CanvasLayer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            # Layer properties
            "layer": self.layer,

            # Transform properties
            "offset": self.offset,
            "rotation": self.rotation,
            "scale": self.scale,

            # Viewport properties
            "follow_viewport_enable": self.follow_viewport_enable,
            "follow_viewport_scale": self.follow_viewport_scale,

            # Custom viewport
            "custom_viewport": self.custom_viewport
        })
        return data


class Scene:
    """Represents a complete scene with nodes"""
    
    def __init__(self, name: str = "Scene"):
        self.name = name
        self.root_nodes = []
        self.metadata = {}
    
    def add_root_node(self, node: Node):
        """Add a root node to the scene"""
        self.root_nodes.append(node)
    
    def remove_root_node(self, node: Node):
        """Remove a root node from the scene"""
        if node in self.root_nodes:
            self.root_nodes.remove(node)
    
    def find_node(self, path: str) -> Optional[Node]:
        """Find a node by path"""
        if '/' not in path:
            # Search in all root nodes
            for root in self.root_nodes:
                if root.name == path:
                    return root
            return None
        
        # Split path and search
        parts = path.split('/', 1)
        root_name = parts[0]
        remaining_path = parts[1]
        
        for root in self.root_nodes:
            if root.name == root_name:
                return root.find_node(remaining_path)
        
        return None
    
    def get_all_nodes(self) -> List[Node]:
        """Get all nodes in the scene (flattened)"""
        nodes = []
        
        def collect_nodes(node: Node):
            nodes.append(node)
            for child in node.children:
                collect_nodes(child)
        
        for root in self.root_nodes:
            collect_nodes(root)
        
        return nodes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scene to dictionary for serialization"""
        return {
            "name": self.name,
            "metadata": self.metadata,
            "nodes": [node.to_dict() for node in self.root_nodes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """Create scene from dictionary"""
        scene = cls(data.get("name", "Scene"))
        scene.metadata = data.get("metadata", {})
        
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            scene.add_root_node(node)
        
        return scene
    
    def save_to_file(self, file_path: str):
        """Save scene to file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['Scene']:
        """Load scene from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Failed to load scene from {file_path}: {e}")
            return None


class SceneManager:
    """Manages scene loading and switching"""
    
    def __init__(self, project: LupineProject):
        self.project = project
        self.current_scene = None
        self.loaded_scenes = {}  # path -> Scene
    
    def load_scene(self, scene_path: str) -> Optional[Scene]:
        """Load a scene from file"""
        if scene_path in self.loaded_scenes:
            return self.loaded_scenes[scene_path]
        
        full_path = self.project.get_absolute_path(scene_path)
        scene = Scene.load_from_file(str(full_path))
        
        if scene:
            self.loaded_scenes[scene_path] = scene
        
        return scene
    
    def save_scene(self, scene: Scene, scene_path: str):
        """Save a scene to file"""
        full_path = self.project.get_absolute_path(scene_path)
        scene.save_to_file(str(full_path))
        
        # Update loaded scenes cache
        self.loaded_scenes[scene_path] = scene
    
    def set_current_scene(self, scene_path: str) -> bool:
        """Set the current active scene"""
        scene = self.load_scene(scene_path)
        if scene:
            self.current_scene = scene
            return True
        return False
    
    def get_current_scene(self) -> Optional[Scene]:
        """Get the current active scene"""
        return self.current_scene
    
    def create_new_scene(self, name: str) -> Scene:
        """Create a new empty scene"""
        scene = Scene(name)
        
        # Add default root node
        root_node = Node2D(name)
        scene.add_root_node(root_node)
        
        return scene
