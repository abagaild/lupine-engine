"""
scene/ui_nodes/color_rect.py

Defines ColorRect (filled rectangle UI element).
"""

from typing import Dict, Any
from .control import Control


class ColorRect(Control):
    """ColorRect: draws a solid colored rectangle."""

    def __init__(self, name: str = "ColorRect"):
        super().__init__(name)
        self.type = "ColorRect"

        self.color: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]
        self.script_path = "nodes/ui/ColorRect.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({"color": self.color})
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorRect":
        node = cls(data.get("name", "ColorRect"))
        node.color = data.get("color", [1.0, 1.0, 1.0, 1.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
