"""
scene/ui_nodes/nine_patch_rect.py

Defines NinePatchRect (resizable image with nine-patch scaling).
"""

from typing import Dict, Any
from .control import Control


class NinePatchRect(Control):
    """NinePatchRect: draws a texture with 9-slice scaling for borders."""

    def __init__(self, name: str = "NinePatchRect"):
        super().__init__(name)
        self.type = "NinePatchRect"

        self.texture: Any = None
        self.region_rect: [int, int, int, int] = [0, 0, 0, 0]
        self.margin_left: float = 0.0
        self.margin_top: float = 0.0
        self.margin_right: float = 0.0
        self.margin_bottom: float = 0.0

        self.script_path = "nodes/ui/NinePatchRect.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "texture": self.texture,
            "region_rect": self.region_rect,
            "margin_left": self.margin_left,
            "margin_top": self.margin_top,
            "margin_right": self.margin_right,
            "margin_bottom": self.margin_bottom
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NinePatchRect":
        node = cls(data.get("name", "NinePatchRect"))
        node.texture = data.get("texture")
        node.region_rect = data.get("region_rect", [0, 0, 0, 0])
        node.margin_left = data.get("margin_left", 0.0)
        node.margin_top = data.get("margin_top", 0.0)
        node.margin_right = data.get("margin_right", 0.0)
        node.margin_bottom = data.get("margin_bottom", 0.0)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
