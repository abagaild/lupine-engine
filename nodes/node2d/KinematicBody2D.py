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

        # Get physics world from scene
        physics_world = self._get_physics_world()
        if not physics_world:
            # Fallback to simple movement
            delta_x = velocity[0] * (1.0/60.0)
            delta_y = velocity[1] * (1.0/60.0)
            self.translate(delta_x, delta_y)
            return velocity.copy()

        # Get our physics body by node reference
        physics_body = physics_world.get_body_by_node(self)
        if not physics_body:
            # Fallback to simple movement if no physics body
            delta_x = velocity[0] * (1.0/60.0)
            delta_y = velocity[1] * (1.0/60.0)
            self.translate(delta_x, delta_y)
            return velocity.copy()

        # Update physics body position to match node position
        physics_body.update_physics_from_node()

        # Calculate movement delta
        delta_time = 1.0 / 60.0
        move_delta = [velocity[0] * delta_time, velocity[1] * delta_time]

        # Try to move and check for collisions using shape casting
        collision_result = self._test_move(physics_body, move_delta, physics_world)

        if collision_result:
            # Collision detected, slide along surface
            normal = collision_result['normal']

            # Calculate slide direction (remove component along normal)
            dot_product = move_delta[0] * normal[0] + move_delta[1] * normal[1]
            slide_delta = [
                move_delta[0] - dot_product * normal[0],
                move_delta[1] - dot_product * normal[1]
            ]

            # Move to collision point
            safe_distance = collision_result['distance'] * 0.99
            safe_move = [move_delta[0] * safe_distance, move_delta[1] * safe_distance]
            self.translate(safe_move[0], safe_move[1])

            # Try to slide along surface
            if abs(slide_delta[0]) > 0.1 or abs(slide_delta[1]) > 0.1:
                slide_result = self._test_move(physics_body, slide_delta, physics_world)
                if not slide_result:
                    self.translate(slide_delta[0], slide_delta[1])

            # Update physics body position after movement
            physics_body.update_physics_from_node()

            # Calculate remaining velocity
            remaining_velocity = [
                velocity[0] - dot_product * normal[0] * 60.0,
                velocity[1] - dot_product * normal[1] * 60.0
            ]
            return remaining_velocity
        else:
            # No collision, move freely
            self.translate(move_delta[0], move_delta[1])
            # Update physics body position after movement
            physics_body.update_physics_from_node()
            return velocity.copy()

    def _test_move(self, physics_body, move_delta, physics_world):
        """Test movement and return collision info if collision would occur"""
        # Get current position
        current_pos = physics_body.pymunk_body.position
        target_pos = (current_pos[0] + move_delta[0], current_pos[1] + move_delta[1])

        # Use raycast to detect collisions along the movement path
        hit = physics_world.raycast(
            (current_pos[0], current_pos[1]),
            target_pos,
            exclude_sensors=True
        )

        if hit:
            return {
                'distance': hit['distance'],
                'normal': hit['normal'],
                'point': hit['point'],
                'body': hit['body']
            }

        return None

    def _get_physics_world(self):
        """Get the physics world from the scene"""
        try:
            # Try to get physics world from scene
            scene = self.get_scene()
            if scene and hasattr(scene, 'physics_world'):
                return scene.physics_world
        except:
            pass
        return None

    def _check_collision_along_path(self, move_delta: List[float], physics_world) -> Optional[Dict[str, Any]]:
        """Check for collisions along movement path using raycast"""
        if not physics_world:
            return None

        # Calculate start and end points for raycast
        start_pos = self.position.copy()
        end_pos = [start_pos[0] + move_delta[0], start_pos[1] + move_delta[1]]

        # Perform raycast
        hit_info = physics_world.raycast((start_pos[0], start_pos[1]), (end_pos[0], end_pos[1]))

        if hit_info and hit_info['body'] and hit_info['body'].node != self:
            return {
                'distance': hit_info['distance'],
                'point': hit_info['point'],
                'normal': hit_info['normal'],
                'body': hit_info['body']
            }

        return None

    def move_and_collide(self, velocity: List[float]) -> Optional[Dict[str, Any]]:
        """
        Move the body and return collision info if collision occurred.
        Returns None if no collision, or collision dict with details.
        """
        # Get physics world
        physics_world = self._get_physics_world()
        if not physics_world:
            # Fallback to simple movement
            delta_x = velocity[0] * (1.0/60.0)
            delta_y = velocity[1] * (1.0/60.0)
            self.translate(delta_x, delta_y)
            return None

        # Calculate movement delta
        delta_time = 1.0 / 60.0
        move_delta = [velocity[0] * delta_time, velocity[1] * delta_time]

        # Check for collision along path
        collision_info = self._check_collision_along_path(move_delta, physics_world)

        # Get our physics body
        physics_body = physics_world.get_body_by_node(self)

        if collision_info:
            # Move to collision point
            safe_distance = collision_info['distance'] * 0.99  # Leave small gap
            safe_delta = [move_delta[0] * safe_distance, move_delta[1] * safe_distance]
            self.translate(safe_delta[0], safe_delta[1])

            # Update physics body position after movement
            if physics_body:
                physics_body.update_physics_from_node()

            # Return collision information
            return {
                'collider': collision_info['body'].node,
                'position': collision_info['point'],
                'normal': collision_info['normal'],
                'travel': safe_delta,
                'remainder': [move_delta[0] - safe_delta[0], move_delta[1] - safe_delta[1]]
            }
        else:
            # No collision, move freely
            self.translate(move_delta[0], move_delta[1])

            # Update physics body position after movement
            if physics_body:
                physics_body.update_physics_from_node()
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
