"""
scene/ui_nodes/texture_rect.py

Defines TextureRect (displays a texture within a rectangle).
"""

from typing import Dict, Any
from .control import Control


class TextureRect(Control):
    """TextureRect: draws a textured rectangle."""

    def __init__(self, name: str = "TextureRect"):
        super().__init__(name)
        self.type = "TextureRect"

        self.texture: Any = None
        self.region_enabled: bool = False
        self.region_rect: [int, int, int, int] = [0, 0, 0, 0]
        self.flip_h: bool = False
        self.flip_v: bool = False

        self.script_path = "nodes/ui/TextureRect.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "texture": self.texture,
            "region_enabled": self.region_enabled,
            "region_rect": self.region_rect,
            "flip_h": self.flip_h,
            "flip_v": self.flip_v
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextureRect":
        node = cls(data.get("name", "TextureRect"))
        node.texture = data.get("texture")
        node.region_enabled = data.get("region_enabled", False)
        node.region_rect = data.get("region_rect", [0, 0, 0, 0])
        node.flip_h = data.get("flip_h", False)
        node.flip_v = data.get("flip_v", False)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
