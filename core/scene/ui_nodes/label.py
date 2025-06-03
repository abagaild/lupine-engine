"""
scene/ui_nodes/label.py

Defines Label (text display) for UI.
"""

from typing import Dict, Any
from .control import Control


class Label(Control):
    """Label displays a line of text with font settings."""

    def __init__(self, name: str = "Label"):
        super().__init__(name)
        self.type = "Label"

        # Text properties
        self.text: str = ""
        self.autowrap: bool = False
        self.align: str = "left"  # left, center, right
        self.valign: str = "top"  # top, center, bottom
        self.font: Any = None
        self.font_size: int = 14
        self.font_color: [float, float, float, float] = [0.0, 0.0, 0.0, 1.0]

        self.script_path = "nodes/ui/Label.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "text": self.text,
            "autowrap": self.autowrap,
            "align": self.align,
            "valign": self.valign,
            "font": self.font,
            "font_size": self.font_size,
            "font_color": self.font_color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Label":
        node = cls(data.get("name", "Label"))
        node.text = data.get("text", "")
        node.autowrap = data.get("autowrap", False)
        node.align = data.get("align", "left")
        node.valign = data.get("valign", "top")
        node.font = data.get("font")
        node.font_size = data.get("font_size", 14)
        node.font_color = data.get("font_color", [0.0, 0.0, 0.0, 1.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
