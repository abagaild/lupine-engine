"""
scene/ui_nodes/progress_bar.py

Defines ProgressBar (horizontal or vertical bar showing progress).
"""

from typing import Dict, Any
from .control import Control


class ProgressBar(Control):
    """ProgressBar: displays a bar that fills up based on value."""

    def __init__(self, name: str = "ProgressBar"):
        super().__init__(name)
        self.type = "ProgressBar"

        self.min_value: float = 0.0
        self.max_value: float = 1.0
        self.value: float = 0.0
        self.orientation: str = "horizontal"  # horizontal or vertical
        self.bar_color: [float, float, float, float] = [0.2, 0.6, 1.0, 1.0]
        self.bg_color: [float, float, float, float] = [0.8, 0.8, 0.8, 1.0]

        self.script_path = "nodes/ui/ProgressBar.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "min_value": self.min_value,
            "max_value": self.max_value,
            "value": self.value,
            "orientation": self.orientation,
            "bar_color": self.bar_color,
            "bg_color": self.bg_color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressBar":
        node = cls(data.get("name", "ProgressBar"))
        node.min_value = data.get("min_value", 0.0)
        node.max_value = data.get("max_value", 1.0)
        node.value = data.get("value", 0.0)
        node.orientation = data.get("orientation", "horizontal")
        node.bar_color = data.get("bar_color", [0.2, 0.6, 1.0, 1.0])
        node.bg_color = data.get("bg_color", [0.8, 0.8, 0.8, 1.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
