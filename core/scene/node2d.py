"""
scene/node2d.py

Defines Node2D (positioned 2D node) as a subclass of Node.
"""

from typing import Dict, Any
from .base_node import Node

# Import Vector2 from builtins for convenience
from core.lsc.builtins import Vector2 as LSCVector2


class Node2D(Node):
    """2D node with transform properties (position, rotation, scale)."""

    def __init__(self, name: str = "Node2D"):
        super().__init__(name, "Node2D")
        # Default transform values
        self.position: LSCVector2 = LSCVector2(0.0, 0.0)
        self.rotation: float = 0.0
        self.scale: LSCVector2 = LSCVector2(1.0, 1.0)
        self.z_index: int = 0
        self.z_as_relative: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()

        # Convert Vector2 to lists for JSON
        pos = [self.position.x, self.position.y]
        scl = [self.scale.x, self.scale.y]
        data.update({
            "position": pos,
            "rotation": self.rotation,
            "scale": scl,
            "z_index": self.z_index,
            "z_as_relative": self.z_as_relative
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node2D":
        node = cls(data.get("name", "Node2D"))
        node.position = LSCVector2(*data.get("position", [0.0, 0.0]))
        node.rotation = data.get("rotation", 0.0)
        node.scale = LSCVector2(*data.get("scale", [1.0, 1.0]))
        node.z_index = data.get("z_index", 0)
        node.z_as_relative = data.get("z_as_relative", True)
        # Apply other common properties
        Node._apply_node_properties(node, data)
        # Reconstruct children
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
