"""
CollisionPolygon2D node implementation for Lupine Engine
Arbitrary polygon collider for complex shapes
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class CollisionPolygon2D(Node2D):
    """
    CollisionPolygon2D: Defines an arbitrary polygon shape for physics.
    Attach as a child of physics bodies or areas.
    """

    def __init__(self, name: str = "CollisionPolygon2D"):
        super().__init__(name)
        self.type = "CollisionPolygon2D"

        # Export variables for editor
        self.export_variables = {
            "polygon": {
                "type": "array",
                "value": [],
                "description": "List of Vector2 points defining the polygon"
            },
            "disabled": {
                "type": "bool",
                "value": False,
                "description": "If true, ignore collisions"
            },
            "one_way_enabled": {
                "type": "bool",
                "value": False,
                "description": "Enable one-way behavior"
            },
            "one_way_collision_margin": {
                "type": "float",
                "value": 0.0,
                "description": "Margin for one-way collisions"
            }
        }

        # Core properties
        self.polygon: List[List[float]] = []  # e.g. [[0,0], [16,0], [16,16], [0,16]]
        self.disabled: bool = False
        self.one_way_enabled: bool = False
        self.one_way_collision_margin: float = 0.0

    def set_polygon(self, points: List[List[float]]):
        """Replace the vertices of the polygon."""
        self.polygon = [p.copy() for p in points]

    def get_polygon(self) -> List[List[float]]:
        """Get a copy of the polygon point list."""
        return [p.copy() for p in self.polygon]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize CollisionPolygon2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "polygon": [pt.copy() for pt in self.polygon],
            "disabled": self.disabled,
            "one_way_enabled": self.one_way_enabled,
            "one_way_collision_margin": self.one_way_collision_margin
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollisionPolygon2D":
        """Deserialize a CollisionPolygon2D from a dictionary."""
        poly = cls(data.get("name", "CollisionPolygon2D"))
        cls._apply_node_properties(poly, data)

        poly.polygon = data.get("polygon", []).copy()
        poly.disabled = data.get("disabled", False)
        poly.one_way_enabled = data.get("one_way_enabled", False)
        poly.one_way_collision_margin = data.get("one_way_collision_margin", 0.0)

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            poly.add_child(child)
        return poly
