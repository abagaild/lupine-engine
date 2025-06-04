"""
Path2D node implementation for Lupine Engine
Defines a Curve2D for path following or drawing
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List


class Path2D(Node2D):
    """
    Path2D: Holds a Curve2D (list of points & handles) to define a path.
    Use PathFollow2D to move along it.
    """

    def __init__(self, name: str = "Path2D"):
        super().__init__(name)
        self.type = "Path2D"

        # Export variables for editor
        self.export_variables = {
            "curve": {
                "type": "array",
                "value": [],
                "description": "List of Vector2 points defining the curve"
            },
            "bake_interval": {
                "type": "float",
                "value": 1.0,
                "description": "Sampling resolution for baked points"
            },
            "show_curve": {
                "type": "bool",
                "value": True,
                "description": "Draw path in-editor"
            }
        }

        # Core properties
        self.curve: List[List[float]] = []  # e.g. [[0,0], [50,30], [100,0]]
        self.bake_interval: float = 1.0
        self.show_curve: bool = True

    def add_point(self, x: float, y: float):
        """Append a point to the curve."""
        self.curve.append([x, y])

    def remove_point(self, index: int):
        """Remove the point at the given index."""
        if 0 <= index < len(self.curve):
            self.curve.pop(index)

    def clear_points(self):
        """Remove all points from the curve."""
        self.curve.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Path2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "curve": [pt.copy() for pt in self.curve],
            "bake_interval": self.bake_interval,
            "show_curve": self.show_curve
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Path2D":
        """Deserialize a Path2D from a dictionary."""
        path = cls(data.get("name", "Path2D"))
        cls._apply_node_properties(path, data)

        path.curve = data.get("curve", []).copy()
        path.bake_interval = data.get("bake_interval", 1.0)
        path.show_curve = data.get("show_curve", True)

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            path.add_child(child)
        return path
