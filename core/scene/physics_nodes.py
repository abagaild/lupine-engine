"""
scene/physics_nodes.py

Defines physics‐related nodes: CollisionShape2D, CollisionPolygon2D,
Area2D, RigidBody2D, StaticBody2D, KinematicBody2D.
"""

from typing import Dict, Any, List
from .node2d import Node2D


class CollisionShape2D(Node2D):
    """2D collision shape node (rectangle, circle, capsule, or segment)."""

    def __init__(self, name: str = "CollisionShape2D"):
        super().__init__(name)
        self.type = "CollisionShape2D"

        # Shape configuration
        self.shape: str = "rectangle"  # rectangle, circle, capsule, segment
        self.size: List[float] = [32.0, 32.0]  # For rectangle
        self.radius: float = 16.0  # For circle and capsule
        self.height: float = 32.0  # Capsule height
        self.from_point: List[float] = [0.0, 0.0]  # For segment
        self.to_point: List[float] = [10.0, 0.0]   # For segment

        # Collision layers and masks
        self.collision_layer: int = 1
        self.collision_mask: int = 1

        self.script_path = "nodes/CollisionShape2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "shape": self.shape,
            "size": self.size,
            "radius": self.radius,
            "height": self.height,
            "from_point": self.from_point,
            "to_point": self.to_point,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollisionShape2D":
        node = cls(data.get("name", "CollisionShape2D"))
        node.shape = data.get("shape", "rectangle")
        node.size = data.get("size", [32.0, 32.0])
        node.radius = data.get("radius", 16.0)
        node.height = data.get("height", 32.0)
        node.from_point = data.get("from_point", [0.0, 0.0])
        node.to_point = data.get("to_point", [10.0, 0.0])
        node.collision_layer = data.get("collision_layer", 1)
        node.collision_mask = data.get("collision_mask", 1)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class CollisionPolygon2D(Node2D):
    """2D collision polygon node (arbitrary polygon shape)."""

    def __init__(self, name: str = "CollisionPolygon2D"):
        super().__init__(name)
        self.type = "CollisionPolygon2D"

        # Polygon points (list of [x, y] pairs)
        self.polygon: List[List[float]] = [[0.0, 0.0], [32.0, 0.0], [32.0, 32.0], [0.0, 32.0]]

        # Collision layers and masks
        self.collision_layer: int = 1
        self.collision_mask: int = 1

        self.script_path = "nodes/CollisionPolygon2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "polygon": self.polygon,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollisionPolygon2D":
        node = cls(data.get("name", "CollisionPolygon2D"))
        node.polygon = data.get("polygon", [[0.0, 0.0], [32.0, 0.0], [32.0, 32.0], [0.0, 32.0]])
        node.collision_layer = data.get("collision_layer", 1)
        node.collision_mask = data.get("collision_mask", 1)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class Area2D(Node2D):
    """2D area node for trigger volumes, detection, and overlap events."""

    def __init__(self, name: str = "Area2D"):
        super().__init__(name)
        self.type = "Area2D"

        # Collision layer and mask
        self.collision_layer: int = 1
        self.collision_mask: int = 1

        # Monitoring properties
        self.monitorable: bool = True
        self.monitoring: bool = False
        self.overlap_only: bool = True

        self.script_path = "nodes/Area2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "monitorable": self.monitorable,
            "monitoring": self.monitoring,
            "overlap_only": self.overlap_only
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Area2D":
        node = cls(data.get("name", "Area2D"))
        node.collision_layer = data.get("collision_layer", 1)
        node.collision_mask = data.get("collision_mask", 1)
        node.monitorable = data.get("monitorable", True)
        node.monitoring = data.get("monitoring", False)
        node.overlap_only = data.get("overlap_only", True)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class RigidBody2D(Node2D):
    """2D rigid body node (dynamic physics)."""

    def __init__(self, name: str = "RigidBody2D"):
        super().__init__(name)
        self.type = "RigidBody2D"

        # Physics body properties
        self.mass: float = 1.0
        self.friction: float = 0.7
        self.elasticity: float = 0.0

        self.collision_layer: int = 1
        self.collision_mask: int = 1

        # Initial velocity
        self.linear_velocity: [float, float] = [0.0, 0.0]
        self.angular_velocity: float = 0.0

        # Sleep / awake
        self.sleeping: bool = False
        self.sleep_threshold: float = 0.1

        self.script_path = "nodes/RigidBody2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "mass": self.mass,
            "friction": self.friction,
            "elasticity": self.elasticity,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "linear_velocity": self.linear_velocity,
            "angular_velocity": self.angular_velocity,
            "sleeping": self.sleeping,
            "sleep_threshold": self.sleep_threshold
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RigidBody2D":
        node = cls(data.get("name", "RigidBody2D"))
        node.mass = data.get("mass", 1.0)
        node.friction = data.get("friction", 0.7)
        node.elasticity = data.get("elasticity", 0.0)
        node.collision_layer = data.get("collision_layer", 1)
        node.collision_mask = data.get("collision_mask", 1)
        node.linear_velocity = data.get("linear_velocity", [0.0, 0.0])
        node.angular_velocity = data.get("angular_velocity", 0.0)
        node.sleeping = data.get("sleeping", False)
        node.sleep_threshold = data.get("sleep_threshold", 0.1)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class StaticBody2D(Node2D):
    """2D static body node (non-dynamic physics, collidable)."""

    def __init__(self, name: str = "StaticBody2D"):
        super().__init__(name)
        self.type = "StaticBody2D"

        self.collision_layer: int = 1
        self.collision_mask: int = 1

        self.script_path = "nodes/StaticBody2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticBody2D":
        node = cls(data.get("name", "StaticBody2D"))
        node.collision_layer = data.get("collision_layer", 1)
        node.collision_mask = data.get("collision_mask", 1)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class KinematicBody2D(Node2D):
    """2D kinematic body node (controlled by user code, not physics)."""

    def __init__(self, name: str = "KinematicBody2D"):
        super().__init__(name)
        self.type = "KinematicBody2D"

        self.collision_layer: int = 1
        self.collision_mask: int = 1

        # Custom velocity set by user script
        self.velocity: [float, float] = [0.0, 0.0]

        self.script_path = "nodes/KinematicBody2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "velocity": self.velocity
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KinematicBody2D":
        node = cls(data.get("name", "KinematicBody2D"))
        node.collision_layer = data.get("collision_layer", 1)
        node.collision_mask = data.get("collision_mask", 1)
        node.velocity = data.get("velocity", [0.0, 0.0])
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
