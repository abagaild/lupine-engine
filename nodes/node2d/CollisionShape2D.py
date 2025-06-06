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
        self.export_variables.update({
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
        })

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

        # Pre-calculated edge normals (outward-facing)
        self._edge_normals: List[List[float]] = []
        self._update_edge_normals()

    def set_shape(self, shape_type: str):
        """Set the shape type (rectangle, circle, capsule, polygon, line)"""
        if shape_type in ["rectangle", "circle", "capsule", "polygon", "line"]:
            self.shape = shape_type
            self._update_edge_normals()
        else:
            print(f"Warning: Invalid shape type '{shape_type}'. Using 'rectangle'.")
            self.shape = "rectangle"
            self._update_edge_normals()

    def set_size(self, width: float, height: float):
        """Set the size for rectangle/capsule shapes"""
        self.size = [max(0.1, width), max(0.1, height)]
        self._update_edge_normals()

    def set_radius(self, radius: float):
        """Set the radius for circle shapes"""
        self.radius = max(0.1, radius)
        self._update_edge_normals()

    def set_height(self, height: float):
        """Set the height for capsule shapes"""
        self.height = max(0.1, height)
        self._update_edge_normals()

    def _update_edge_normals(self):
        """Calculate and store outward-facing normals for each edge of the shape"""
        import math

        self._edge_normals = []

        if self.shape == "rectangle":
            # Rectangle has 4 edges with known normals
            # Top edge: normal points up (0, -1)
            # Right edge: normal points right (1, 0)
            # Bottom edge: normal points down (0, 1)
            # Left edge: normal points left (-1, 0)
            self._edge_normals = [
                [0.0, -1.0],  # Top edge (floor when player is above)
                [1.0, 0.0],   # Right edge (wall)
                [0.0, 1.0],   # Bottom edge (ceiling when player is below)
                [-1.0, 0.0]   # Left edge (wall)
            ]

        elif self.shape == "polygon":
            # Calculate normals for each edge of the polygon
            points = self.points
            num_points = len(points)

            for i in range(num_points):
                # Get current point and next point (wrapping around)
                p1 = points[i]
                p2 = points[(i + 1) % num_points]

                # Calculate edge vector
                edge_x = p2[0] - p1[0]
                edge_y = p2[1] - p1[1]

                # Calculate outward normal (perpendicular to edge, pointing outward)
                # For a polygon with vertices in counter-clockwise order,
                # the outward normal is (-edge_y, edge_x)
                normal_x = -edge_y
                normal_y = edge_x

                # Normalize the normal vector
                length = math.sqrt(normal_x * normal_x + normal_y * normal_y)
                if length > 0.001:
                    normal_x /= length
                    normal_y /= length
                else:
                    # Degenerate edge, use default normal
                    normal_x, normal_y = 0.0, -1.0

                self._edge_normals.append([normal_x, normal_y])

        elif self.shape == "line":
            # Line has one edge with a normal perpendicular to it
            start = self.line_start
            end = self.line_end

            # Calculate line vector
            line_x = end[0] - start[0]
            line_y = end[1] - start[1]

            # Calculate perpendicular normal (there are two choices, pick one)
            normal_x = -line_y
            normal_y = line_x

            # Normalize
            length = math.sqrt(normal_x * normal_x + normal_y * normal_y)
            if length > 0.001:
                normal_x /= length
                normal_y /= length
            else:
                normal_x, normal_y = 0.0, -1.0

            self._edge_normals.append([normal_x, normal_y])

        elif self.shape == "circle":
            # Circles don't have discrete edges, but we can approximate
            # The normal at any point on a circle points radially outward
            # We'll store this as a special case and handle it differently
            self._edge_normals = [[0.0, 0.0]]  # Special marker for circle

        elif self.shape == "capsule":
            # Capsules are like rectangles with rounded ends
            # Use rectangle normals for the main body
            self._edge_normals = [
                [0.0, -1.0],  # Top edge
                [1.0, 0.0],   # Right edge
                [0.0, 1.0],   # Bottom edge
                [-1.0, 0.0]   # Left edge
            ]

    def get_edge_normals(self) -> List[List[float]]:
        """Get the pre-calculated outward-facing edge normals"""
        return self._edge_normals.copy()

    def get_best_collision_normal(self, collision_point: List[float], other_center: List[float]) -> List[float]:
        """
        Get the best collision normal based on collision point and the other object's center.
        This provides more accurate normals than center-to-center calculation.
        """
        import math

        if self.shape == "circle":
            # For circles, normal points from circle center to collision point
            center = self.get_global_position()
            dx = collision_point[0] - center[0]
            dy = collision_point[1] - center[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0.001:
                return [dx/length, dy/length]
            else:
                return [0.0, 1.0]  # Default upward

        elif self.shape == "rectangle":
            # For rectangles, determine which edge is closest to collision point
            center = self.get_global_position()
            width, height = self.size[0], self.size[1]

            # Calculate relative position from center
            rel_x = collision_point[0] - center[0]
            rel_y = collision_point[1] - center[1]

            # Determine which edge based on which boundary is closest
            # Normalize to half-extents
            norm_x = rel_x / (width / 2) if width > 0 else 0
            norm_y = rel_y / (height / 2) if height > 0 else 0

            # Find the edge with maximum normalized distance
            abs_norm_x = abs(norm_x)
            abs_norm_y = abs(norm_y)

            if abs_norm_x > abs_norm_y:
                # Collision is on left or right edge
                return [1.0, 0.0] if norm_x > 0 else [-1.0, 0.0]
            else:
                # Collision is on top or bottom edge
                return [0.0, 1.0] if norm_y > 0 else [0.0, -1.0]

        elif self.shape == "polygon":
            # For polygons, find the closest edge and return its normal
            min_distance = float('inf')
            best_normal = [0.0, 1.0]

            points = self.points
            num_points = len(points)

            for i in range(num_points):
                p1 = points[i]
                p2 = points[(i + 1) % num_points]

                # Calculate distance from collision point to this edge
                distance = self._point_to_line_distance(collision_point, p1, p2)

                if distance < min_distance:
                    min_distance = distance
                    best_normal = self._edge_normals[i].copy()

            return best_normal

        else:
            # Default case
            return [0.0, 1.0]

    def _point_to_line_distance(self, point: List[float], line_start: List[float], line_end: List[float]) -> float:
        """Calculate the distance from a point to a line segment"""
        import math

        # Vector from line_start to line_end
        line_vec_x = line_end[0] - line_start[0]
        line_vec_y = line_end[1] - line_start[1]

        # Vector from line_start to point
        point_vec_x = point[0] - line_start[0]
        point_vec_y = point[1] - line_start[1]

        # Project point onto line
        line_length_sq = line_vec_x * line_vec_x + line_vec_y * line_vec_y

        if line_length_sq < 0.001:
            # Degenerate line, return distance to start point
            dx = point[0] - line_start[0]
            dy = point[1] - line_start[1]
            return math.sqrt(dx*dx + dy*dy)

        # Calculate projection parameter
        t = (point_vec_x * line_vec_x + point_vec_y * line_vec_y) / line_length_sq
        t = max(0.0, min(1.0, t))  # Clamp to line segment

        # Find closest point on line segment
        closest_x = line_start[0] + t * line_vec_x
        closest_y = line_start[1] + t * line_vec_y

        # Return distance
        dx = point[0] - closest_x
        dy = point[1] - closest_y
        return math.sqrt(dx*dx + dy*dy)

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
            "debug_color": self.debug_color.copy(),
            "_edge_normals": [normal.copy() for normal in self._edge_normals]
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollisionShape2D":
        """Deserialize a CollisionShape2D from a dictionary."""
        shape = cls(data.get("name", "CollisionShape2D"))
        cls._apply_node_properties(shape, data)

        # Apply Node2D specific properties (position, rotation, scale, etc.)
        shape.position = data.get("position", [0.0, 0.0])
        shape.rotation = data.get("rotation", 0.0)
        shape.scale = data.get("scale", [1.0, 1.0])
        shape.z_index = data.get("z_index", 0)
        shape.z_as_relative = data.get("z_as_relative", True)

        # Apply CollisionShape2D specific properties
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

        # Restore edge normals if available, otherwise recalculate
        if "_edge_normals" in data:
            shape._edge_normals = [normal.copy() for normal in data["_edge_normals"]]
        else:
            shape._update_edge_normals()

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            shape.add_child(child)
        return shape
