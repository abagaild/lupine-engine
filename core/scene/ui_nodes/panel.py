"""
scene/ui_nodes/panel.py

Defines Panel (a basic UI container with background).
"""

from typing import Dict, Any
from .control import Control


class Panel(Control):
    """Panel container: draws a background and border."""

    def __init__(self, name: str = "Panel"):
        super().__init__(name)
        self.type = "Panel"

        # Style
        self.panel_min_size: [float, float] = [0.0, 0.0]
        self.panel_margin: [float, float, float, float] = [4.0, 4.0, 4.0, 4.0]
        self.border_width: float = 1.0
        self.border_color: [float, float, float, float] = [0.5, 0.5, 0.5, 1.0]
        self.background_color: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]

        self.script_path = "nodes/ui/Panel.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "panel_min_size": self.panel_min_size,
            "panel_margin": self.panel_margin,
            "border_width": self.border_width,
            "border_color": self.border_color,
            "background_color": self.background_color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Panel":
        node = cls(data.get("name", "Panel"))
        node.panel_min_size = data.get("panel_min_size", [0.0, 0.0])
        node.panel_margin = data.get("panel_margin", [4.0, 4.0, 4.0, 4.0])
        node.border_width = data.get("border_width", 1.0)
        node.border_color = data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        node.background_color = data.get("background_color", [1.0, 1.0, 1.0, 1.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
