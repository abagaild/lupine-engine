"""
scene/ui_nodes/slider.py

Defines Slider (horizontal or vertical value slider).
"""

from typing import Dict, Any
from .control import Control


class Slider(Control):
    """Slider: allows the user to select a value within a range."""

    def __init__(self, name: str = "Slider"):
        super().__init__(name)
        self.type = "Slider"

        self.min_value: float = 0.0
        self.max_value: float = 1.0
        self.value: float = 0.0
        self.step: float = 0.1
        self.orientation: str = "horizontal"  # horizontal or vertical

        self.page: float = 0.0  # page scroll value
        self.handle_size: float = 10.0

        self.script_path = "nodes/ui/Slider.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "min_value": self.min_value,
            "max_value": self.max_value,
            "value": self.value,
            "step": self.step,
            "orientation": self.orientation,
            "page": self.page,
            "handle_size": self.handle_size
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Slider":
        node = cls(data.get("name", "Slider"))
        node.min_value = data.get("min_value", 0.0)
        node.max_value = data.get("max_value", 1.0)
        node.value = data.get("value", 0.0)
        node.step = data.get("step", 0.1)
        node.orientation = data.get("orientation", "horizontal")
        node.page = data.get("page", 0.0)
        node.handle_size = data.get("handle_size", 10.0)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
