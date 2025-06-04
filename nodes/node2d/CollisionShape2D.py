"""
CollisionShape2D node implementation for Lupine Engine
Basic collision shapes for physics bodies
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class CollisionShape2D(Node2D):
    """
    CollisionShape2D: Defines basic collision shapes for physics.
    Attach as a child of physics bodies or areas.
    Supports rectangle, circle, and capsule shapes.
    """

    def __init__(self, name: str = "CollisionShape2D"):
        super().__init__(name)
        self.type = "CollisionShape2D"

        # Export variables for editor
        self.export_variables = {
            "shape": {
                "type": "enum",
                "value": "rectangle",
                "options": ["rectangle", "circle", "capsule", "polygon", "line"],
                "description": "Type of collision shape"
            },
            "size": {
                "type": "vector2",
                "value": [32.0, 32.0],
                "description": "Size of rectangle/capsule shape"
            },
            "radius": {
                "type": "float",
                "value": 16.0,
                "description": "Radius for circle shape"
            },
            "height": {
                "type": "float",
                "value": 32.0,
                "description": "Height for capsule shape"
            },
            "points": {
                "type": "array",
                "value": [[0, 0], [32, 0], [32, 32], [0, 32]],
                "description": "Points for polygon shape (local coordinates)"
            },
            "line_start": {
                "type": "vector2",
                "value": [0.0, 0.0],
                "description": "Start point for line shape"
            },
            "line_end": {
                "type": "vector2",
                "value": [32.0, 0.0],
                "description": "End point for line shape"
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
            },
            "debug_color": {
                "type": "color",
                "value": [0.0, 0.6, 0.7, 0.5],
                "description": "Color for debug visualization"
            }
        }

        # Core properties
        self.shape: str = "rectangle"  # rectangle, circle, capsule, polygon, line
        self.size: List[float] = [32.0, 32.0]  # width, height for rectangle/capsule
        self.radius: float = 16.0  # radius for circle
        self.height: float = 32.0  # height for capsule
        self.points: List[List[float]] = [[0, 0], [32, 0], [32, 32], [0, 32]]  # polygon points
        self.line_start: List[float] = [0.0, 0.0]  # line start point
        self.line_end: List[float] = [32.0, 0.0]  # line end point
        self.disabled: bool = False
        self.one_way_enabled: bool = False
        self.one_way_collision_margin: float = 0.0
        self.debug_color: List[float] = [0.0, 0.6, 0.7, 0.5]

    def set_shape(self, shape_type: str):
        """Set the shape type (rectangle, circle, capsule, polygon, line)"""
        if shape_type in ["rectangle", "circle", "capsule", "polygon", "line"]:
            self.shape = shape_type
        else:
            print(f"Warning: Invalid shape type '{shape_type}'. Using 'rectangle'.")
            self.shape = "rectangle"

    def set_size(self, width: float, height: float):
        """Set the size for rectangle/capsule shapes"""
        self.size = [max(0.1, width), max(0.1, height)]

    def set_radius(self, radius: float):
        """Set the radius for circle shapes"""
        self.radius = max(0.1, radius)

    def set_height(self, height: float):
        """Set the height for capsule shapes"""
        self.height = max(0.1, height)

    def set_points(self, points: List[List[float]]):
        """Set the points for polygon shapes"""
        if len(points) >= 3:
            self.points = points.copy()
        else:
            print("Warning: Polygon must have at least 3 points")

    def add_point(self, x: float, y: float):
        """Add a point to polygon shape"""
        self.points.append([x, y])

    def remove_point(self, index: int):
        """Remove a point from polygon shape"""
        if 0 <= index < len(self.points) and len(self.points) > 3:
            self.points.pop(index)
        else:
            print("Warning: Cannot remove point - polygon must have at least 3 points")

    def set_line(self, start_x: float, start_y: float, end_x: float, end_y: float):
        """Set the line endpoints"""
        self.line_start = [start_x, start_y]
        self.line_end = [end_x, end_y]

    def get_shape_bounds(self) -> Dict[str, float]:
        """Get the bounding box of this shape"""
        if self.shape == "rectangle":
            return {
                "left": -self.size[0] / 2,
                "right": self.size[0] / 2,
                "top": -self.size[1] / 2,
                "bottom": self.size[1] / 2
            }
        elif self.shape == "circle":
            return {
                "left": -self.radius,
                "right": self.radius,
                "top": -self.radius,
                "bottom": self.radius
            }
        elif self.shape == "capsule":
            # Capsule is like a rectangle with rounded ends
            return {
                "left": -self.size[0] / 2,
                "right": self.size[0] / 2,
                "top": -self.height / 2,
                "bottom": self.height / 2
            }
        elif self.shape == "polygon":
            if not self.points:
                return {"left": 0, "right": 0, "top": 0, "bottom": 0}
            min_x = min(point[0] for point in self.points)
            max_x = max(point[0] for point in self.points)
            min_y = min(point[1] for point in self.points)
            max_y = max(point[1] for point in self.points)
            return {
                "left": min_x,
                "right": max_x,
                "top": min_y,
                "bottom": max_y
            }
        elif self.shape == "line":
            min_x = min(self.line_start[0], self.line_end[0])
            max_x = max(self.line_start[0], self.line_end[0])
            min_y = min(self.line_start[1], self.line_end[1])
            max_y = max(self.line_start[1], self.line_end[1])
            return {
                "left": min_x,
                "right": max_x,
                "top": min_y,
                "bottom": max_y
            }
        return {"left": 0, "right": 0, "top": 0, "bottom": 0}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize CollisionShape2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "shape": self.shape,
            "size": self.size.copy(),
            "radius": self.radius,
            "height": self.height,
            "points": [point.copy() for point in self.points],
            "line_start": self.line_start.copy(),
            "line_end": self.line_end.copy(),
            "disabled": self.disabled,
            "one_way_enabled": self.one_way_enabled,
            "one_way_collision_margin": self.one_way_collision_margin,
            "debug_color": self.debug_color.copy()
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollisionShape2D":
        """Deserialize a CollisionShape2D from a dictionary."""
        shape = cls(data.get("name", "CollisionShape2D"))
        cls._apply_node_properties(shape, data)

        shape.shape = data.get("shape", "rectangle")
        shape.size = data.get("size", [32.0, 32.0]).copy()
        shape.radius = data.get("radius", 16.0)
        shape.height = data.get("height", 32.0)
        shape.points = [point.copy() for point in data.get("points", [[0, 0], [32, 0], [32, 32], [0, 32]])]
        shape.line_start = data.get("line_start", [0.0, 0.0]).copy()
        shape.line_end = data.get("line_end", [32.0, 0.0]).copy()
        shape.disabled = data.get("disabled", False)
        shape.one_way_enabled = data.get("one_way_enabled", False)
        shape.one_way_collision_margin = data.get("one_way_collision_margin", 0.0)
        shape.debug_color = data.get("debug_color", [0.0, 0.6, 0.7, 0.5]).copy()

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            shape.add_child(child)
        return shape
