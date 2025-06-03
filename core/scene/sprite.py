"""
scene/sprite.py

Defines Sprite and AnimatedSprite nodes (2D textured nodes).
"""

from typing import Dict, Any
from .node2d import Node2D, Node


class Sprite(Node2D):
    """Sprite node for displaying a single texture."""

    def __init__(self, name: str = "Sprite"):
        super().__init__(name)
        self.type = "Sprite"

        # Texture fields
        self.texture: Any = None
        self.normal_map: Any = None

        # Transform info
        self.centered: bool = True
        self.offset: [float, float] = [0.0, 0.0]
        self.flip_h: bool = False
        self.flip_v: bool = False

        # Region fields (texture atlas)
        self.region_enabled: bool = False
        self.region_rect: [int, int, int, int] = [0, 0, 0, 0]
        self.region_filter_clip: bool = False

        # Animation frames (for sprite sheets)
        self.hframes: int = 1
        self.vframes: int = 1
        self.frame: int = 0
        self.frame_coords: [int, int] = [0, 0]

        # Rendering modulation
        self.modulate: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]
        self.self_modulate: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]

        # Default script for this node
        self.script_path = "nodes/Sprite.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "texture": self.texture,
            "normal_map": self.normal_map,
            "centered": self.centered,
            "offset": self.offset,
            "flip_h": self.flip_h,
            "flip_v": self.flip_v,
            "region_enabled": self.region_enabled,
            "region_rect": self.region_rect,
            "region_filter_clip": self.region_filter_clip,
            "hframes": self.hframes,
            "vframes": self.vframes,
            "frame": self.frame,
            "frame_coords": self.frame_coords,
            "modulate": self.modulate,
            "self_modulate": self.self_modulate
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sprite":
        node = cls(data.get("name", "Sprite"))
        node.texture = data.get("texture")
        node.normal_map = data.get("normal_map")
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
        node.frame_coords = data.get("frame_coords", [0, 0])
        node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        node.self_modulate = data.get("self_modulate", [1.0, 1.0, 1.0, 1.0])
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class AnimatedSprite(Sprite):
    """AnimatedSprite node for displaying multi-frame animations."""

    def __init__(self, name: str = "AnimatedSprite"):
        super().__init__(name)
        self.type = "AnimatedSprite"

        # Animation-specific fields
        self.sprite_frames: Any = None  # Reference to a SpriteFrames resource
        self.animation: str = "default"
        self.speed_scale: float = 1.0
        self.playing: bool = False
        self.autoplay: str = ""
        self.frame_progress: float = 0.0

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimatedSprite":
        node = cls(data.get("name", "AnimatedSprite"))
        node.sprite_frames = data.get("sprite_frames")
        node.animation = data.get("animation", "default")
        node.speed_scale = data.get("speed_scale", 1.0)
        node.playing = data.get("playing", False)
        node.autoplay = data.get("autoplay", "")
        node.frame_progress = data.get("frame_progress", 0.0)
        return Sprite.from_dict(data)  # reuses parent’s from_dict logic
