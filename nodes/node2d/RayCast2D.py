"""
RayCast2D node implementation for Lupine Engine
Casts a ray each frame to detect the first collider
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class RayCast2D(Node2D):
    """
    RayCast2D: Casts a 2D ray from origin toward cast_to each frame.
    Reports first collision point, normal, and collider reference.
    """

    def __init__(self, name: str = "RayCast2D"):
        super().__init__(name)
        self.type = "RayCast2D"

        # Export variables for editor
        self.export_variables = {
            "cast_to": {
                "type": "vector2",
                "value": [100.0, 0.0],
                "description": "Endpoint of the ray in local space"
            },
            "enabled": {
                "type": "bool",
                "value": True,
                "description": "Whether to cast this ray each frame"
            },
            "collision_layer": {
                "type": "int",
                "value": 1,
                "description": "Which layers to detect collisions against"
            },
            "collision_mask": {
                "type": "int",
                "value": 1,
                "description": "Which layers to ignore"
            },
            "exclude_parent": {
                "type": "bool",
                "value": True,
                "description": "Ignore collisions with the parent node"
            }
        }

        # Core properties
        self.cast_to: List[float] = [100.0, 0.0]
        self.enabled: bool = True
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self.exclude_parent: bool = True

        # Runtime hit info
        self._is_colliding: bool = False
        self._collision_point: List[float] = [0.0, 0.0]
        self._collision_normal: List[float] = [0.0, 0.0]
        self._collider: Optional[Node2D] = None

    def _process(self, delta: float):
        """Perform a raycast each frame if enabled."""
        super()._process(delta)
        if not self.enabled:
            self._is_colliding = False
            self._collider = None
            return

        # Perform raycast
        self._perform_raycast()

    def is_colliding(self) -> bool:
        """Read-only: whether the ray is currently colliding."""
        return self._is_colliding

    def get_collision_point(self) -> List[float]:
        """Read-only: world position where the ray hits."""
        return self._collision_point.copy()

    def get_collision_normal(self) -> List[float]:
        """Read-only: normal of the surface hit."""
        return self._collision_normal.copy()

    def get_collider(self) -> Optional[Node2D]:
        """Read-only: reference to the node hit (if any)."""
        return self._collider

    def force_raycast_update(self):
        """Force an immediate raycast update"""
        if self.enabled:
            self._perform_raycast()

    def _perform_raycast(self):
        """Perform the actual raycast operation"""
        # In a full implementation, this would:
        # 1. Get global start position (self.global_position)
        # 2. Calculate global end position (start + cast_to)
        # 3. Query physics world for intersections
        # 4. Filter by collision_mask and exclude_parent
        # 5. Set collision results

        # For now: simplified stub implementation
        self._is_colliding = False
        self._collider = None
        self._collision_point = [0.0, 0.0]
        self._collision_normal = [0.0, 0.0]

        # TODO: Integrate with physics system for actual raycasting

    def set_cast_to(self, x: float, y: float):
        """Set the cast direction and distance"""
        self.cast_to = [x, y]

    def get_cast_to(self) -> List[float]:
        """Get the cast direction and distance"""
        return self.cast_to.copy()

    def set_enabled(self, enabled: bool):
        """Enable or disable the raycast"""
        self.enabled = enabled
        if not enabled:
            self._is_colliding = False
            self._collider = None

    def is_enabled(self) -> bool:
        """Check if the raycast is enabled"""
        return self.enabled

    def add_exception(self, node: 'Node2D'):
        """Add a node to exclude from raycasting"""
        # In a full implementation, maintain an exclusion list
        pass

    def remove_exception(self, node: 'Node2D'):
        """Remove a node from the exclusion list"""
        # In a full implementation, remove from exclusion list
        pass

    def clear_exceptions(self):
        """Clear all exceptions"""
        # In a full implementation, clear exclusion list
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize RayCast2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "cast_to": self.cast_to.copy(),
            "enabled": self.enabled,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "exclude_parent": self.exclude_parent
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RayCast2D":
        """Deserialize a RayCast2D from a dictionary."""
        ray = cls(data.get("name", "RayCast2D"))
        cls._apply_node_properties(ray, data)

        ray.cast_to = data.get("cast_to", [100.0, 0.0])
        ray.enabled = data.get("enabled", True)
        ray.collision_layer = data.get("collision_layer", 1)
        ray.collision_mask = data.get("collision_mask", 1)
        ray.exclude_parent = data.get("exclude_parent", True)

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            ray.add_child(child)
        return ray
