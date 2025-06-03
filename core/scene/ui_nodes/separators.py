"""
scene/ui_nodes/separators.py

Defines HSeparator and VSeparator (horizontal/vertical lines).
"""

from typing import Dict, Any
from .control import Control


class HSeparator(Control):
    """HSeparator: draws a horizontal line across the width of the container."""

    def __init__(self, name: str = "HSeparator"):
        super().__init__(name)
        self.type = "HSeparator"

        self.width: float = 100.0
        self.height: float = 2.0
        self.color: [float, float, float, float] = [0.5, 0.5, 0.5, 1.0]

        self.script_path = "nodes/ui/HSeparator.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "width": self.width,
            "height": self.height,
            "color": self.color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HSeparator":
        node = cls(data.get("name", "HSeparator"))
        node.width = data.get("width", 100.0)
        node.height = data.get("height", 2.0)
        node.color = data.get("color", [0.5, 0.5, 0.5, 1.0])
        Control._apply_node_properties(node, data)
        return node


class VSeparator(Control):
    """VSeparator: draws a vertical line across the height of the container."""

    def __init__(self, name: str = "VSeparator"):
        super().__init__(name)
        self.type = "VSeparator"

        self.width: float = 2.0
        self.height: float = 100.0
        self.color: [float, float, float, float] = [0.5, 0.5, 0.5, 1.0]

        self.script_path = "nodes/ui/VSeparator.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "width": self.width,
            "height": self.height,
            "color": self.color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VSeparator":
        node = cls(data.get("name", "VSeparator"))
        node.width = data.get("width", 2.0)
        node.height = data.get("height", 100.0)
        node.color = data.get("color", [0.5, 0.5, 0.5, 1.0])
        Control._apply_node_properties(node, data)
        return node
