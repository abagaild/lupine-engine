"""
StaticBody2D node implementation for Lupine Engine
Non-moving physics body for floors/walls
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class StaticBody2D(Node2D):
    """
    StaticBody2D: A non-moving physics object.
    Use for floors, walls, or any immovable obstacle.
    It expects child Collider nodes (CollisionShape2D or CollisionPolygon2D).
    """

    def __init__(self, name: str = "StaticBody2D"):
        super().__init__(name)
        self.type = "StaticBody2D"

        # Export variables for editor
        self.export_variables = {
            "collision_layer": {
                "type": "int",
                "value": 1,
                "description": "Which physics layer this body occupies"
            },
            "collision_mask": {
                "type": "int",
                "value": 1,
                "description": "Which layers this body collides with"
            },
            "one_way_collision_enabled": {
                "type": "bool",
                "value": False,
                "description": "Enable one-way collisions (e.g. platforms)"
            },
            "one_way_collision_margin": {
                "type": "float",
                "value": 0.0,
                "description": "Margin allowed on one-way collision"
            }
        }

        # Core properties
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self.one_way_collision_enabled: bool = False
        self.one_way_collision_margin: float = 0.0

        # Built-in signals
        self.add_signal("body_entered")
        self.add_signal("body_exited")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize StaticBody2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "one_way_collision_enabled": self.one_way_collision_enabled,
            "one_way_collision_margin": self.one_way_collision_margin
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticBody2D":
        """Deserialize a StaticBody2D from a dictionary."""
        body = cls(data.get("name", "StaticBody2D"))
        cls._apply_node_properties(body, data)

        # Apply Node2D specific properties (position, rotation, scale)
        body.position = data.get("position", [0.0, 0.0])
        body.rotation = data.get("rotation", 0.0)
        body.scale = data.get("scale", [1.0, 1.0])
        body.z_index = data.get("z_index", 0)
        body.z_as_relative = data.get("z_as_relative", True)
        body.visible = data.get("visible", True)

        body.collision_layer = data.get("collision_layer", 1)
        body.collision_mask = data.get("collision_mask", 1)
        body.one_way_collision_enabled = data.get("one_way_collision_enabled", False)
        body.one_way_collision_margin = data.get("one_way_collision_margin", 0.0)

        # Re-create children using proper scene loading
        for child_data in data.get("children", []):
            try:
                # Use the scene manager's node creation method for proper type handling
                from core.scene.scene_manager import Scene
                child = Scene._create_node_from_dict(child_data)
                body.add_child(child)
            except ImportError:
                # Fallback to base Node
                from nodes.base.Node import Node
                child = Node.from_dict(child_data)
                body.add_child(child)
        return body
