"""
KinematicBody2D node implementation for Lupine Engine
Manually-controlled physics body (move_and_collide, move_and_slide)
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class KinematicBody2D(Node2D):
    """
    KinematicBody2D: A physics body you drive via code.
    Use move_and_collide() or move_and_slide() to handle collisions.
    """

    def __init__(self, name: str = "KinematicBody2D"):
        super().__init__(name)
        self.type = "KinematicBody2D"

        # Export variables for editor
        self.export_variables = {
            "collision_layer": {
                "type": "int",
                "value": 1,
                "description": "Which layer this body occupies"
            },
            "collision_mask": {
                "type": "int",
                "value": 1,
                "description": "Which layers this body collides with"
            },
            "floor_max_angle": {
                "type": "float",
                "value": 45.0,
                "description": "Maximum slope angle (degrees) to consider as floor"
            },
            "max_speed": {
                "type": "float",
                "value": 200.0,
                "description": "Reference max speed (for scripts)"
            },
            "gravity_scale": {
                "type": "float",
                "value": 1.0,
                "description": "Multiplier on global gravity"
            },
            "friction": {
                "type": "float",
                "value": 0.5,
                "description": "Friction when on floor (for move_and_slide)"
            },
            "bounce": {
                "type": "float",
                "value": 0.0,
                "description": "Restitution when colliding"
            }
        }

        # Core properties
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self.floor_max_angle: float = 45.0
        self.max_speed: float = 200.0
        self.gravity_scale: float = 1.0
        self.friction: float = 0.5
        self.bounce: float = 0.0

        # Playback state for move_and_slide (stubbed)
        self._velocity: List[float] = [0.0, 0.0]

        # Built-in signals
        self.add_signal("body_entered")
        self.add_signal("body_exited")

    def move_and_slide(self, velocity: List[float], floor_normal: Optional[List[float]] = None) -> List[float]:
        """
        Move the body and slide along collisions.
        Returns the remaining velocity after collisions.
        """
        self._velocity = velocity.copy()

        # In a full implementation, this would:
        # 1. Cast the body along the velocity vector
        # 2. Find the first collision
        # 3. Move to the collision point
        # 4. Calculate slide vector along the collision surface
        # 5. Repeat with remaining velocity

        # For now: simplified movement with basic collision response
        remaining_velocity = velocity.copy()

        # Apply movement (simplified)
        delta_x = velocity[0] * (1.0/60.0)  # Assume 60 FPS
        delta_y = velocity[1] * (1.0/60.0)

        # Move and check for collisions (stub)
        old_pos = self.position.copy()
        self.translate(delta_x, delta_y)

        # In a real implementation, check for collisions here
        # and adjust position/velocity accordingly

        return remaining_velocity

    def move_and_collide(self, velocity: List[float]) -> Optional[Dict[str, Any]]:
        """
        Move the body and return collision info if collision occurred.
        Returns None if no collision, or collision dict with details.
        """
        # Store old position
        old_pos = self.position.copy()

        # Calculate movement
        delta_x = velocity[0] * (1.0/60.0)  # Assume 60 FPS
        delta_y = velocity[1] * (1.0/60.0)

        # Apply movement
        self.translate(delta_x, delta_y)

        # In a full implementation, this would:
        # 1. Cast the body along the velocity vector
        # 2. Check for collisions with other physics bodies
        # 3. Return collision information if collision occurred

        # For now: return None (no collision detected)
        return None

    def is_on_floor(self) -> bool:
        """Check if the body is on the floor"""
        # In a full implementation, this would check for floor collisions
        # based on the floor_max_angle and collision normals
        return False

    def is_on_wall(self) -> bool:
        """Check if the body is touching a wall"""
        # In a full implementation, this would check for wall collisions
        return False

    def is_on_ceiling(self) -> bool:
        """Check if the body is touching the ceiling"""
        # In a full implementation, this would check for ceiling collisions
        return False

    def get_floor_normal(self) -> List[float]:
        """Get the normal vector of the floor surface"""
        # In a full implementation, this would return the actual floor normal
        return [0.0, -1.0]  # Default upward normal

    def get_wall_normal(self) -> List[float]:
        """Get the normal vector of the wall surface"""
        # In a full implementation, this would return the actual wall normal
        return [1.0, 0.0]  # Default right-facing normal

    def to_dict(self) -> Dict[str, Any]:
        """Serialize KinematicBody2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "floor_max_angle": self.floor_max_angle,
            "max_speed": self.max_speed,
            "gravity_scale": self.gravity_scale,
            "friction": self.friction,
            "bounce": self.bounce,
            "_velocity": self._velocity.copy()
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KinematicBody2D":
        """Deserialize a KinematicBody2D from a dictionary."""
        body = cls(data.get("name", "KinematicBody2D"))

        # Apply Node2D properties using parent's from_dict logic
        # This ensures position, rotation, scale are properly set
        from nodes.base.Node2D import Node2D
        Node2D._apply_node_properties(body, data)

        # Apply Node2D specific properties
        body.position = data.get("position", [0.0, 0.0])
        body.rotation = data.get("rotation", 0.0)
        body.scale = data.get("scale", [1.0, 1.0])
        body.z_index = data.get("z_index", 0)
        body.z_as_relative = data.get("z_as_relative", True)
        body.visible = data.get("visible", True)

        # Apply KinematicBody2D specific properties
        body.collision_layer = data.get("collision_layer", 1)
        body.collision_mask = data.get("collision_mask", 1)
        body.floor_max_angle = data.get("floor_max_angle", 45.0)
        body.max_speed = data.get("max_speed", 200.0)
        body.gravity_scale = data.get("gravity_scale", 1.0)
        body.friction = data.get("friction", 0.5)
        body.bounce = data.get("bounce", 0.0)
        body._velocity = data.get("_velocity", [0.0, 0.0])

        # Re-create children using proper node loading
        for child_data in data.get("children", []):
            try:
                # Try to use the scene manager's node creation method
                from core.scene.scene_manager import Scene
                child = Scene._create_node_from_dict(child_data)
                body.add_child(child)
            except ImportError:
                # Fallback to base Node
                from nodes.base.Node import Node
                child = Node.from_dict(child_data)
                body.add_child(child)
        return body
