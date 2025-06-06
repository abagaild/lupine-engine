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
        self._last_motion: List[float] = [0.0, 0.0]  # Track last movement for emergency escape
        self._collision_cushion: float = 2.0  # Safety margin to prevent constant emergency escapes
        self._emergency_escape_cooldown: float = 0.0  # Cooldown timer for emergency escapes

        # Collision state tracking for is_on_floor/wall/ceiling detection
        self._collision_state: Dict[str, Any] = {
            'on_floor': False,
            'on_wall': False,
            'on_ceiling': False,
            'floor_normal': [0.0, 1.0],  # Floor normal points UP (correct)
            'wall_normal': [1.0, 0.0],
            'ceiling_normal': [0.0, -1.0],  # Ceiling normal points DOWN (correct)
            'last_floor_time': 0.0,
            'last_wall_time': 0.0,
            'last_ceiling_time': 0.0
        }

        # Built-in signals
        self.add_signal("body_entered")
        self.add_signal("body_exited")

    def move_and_slide(self, velocity: List[float], floor_normal: Optional[List[float]] = None) -> List[float]:
        """
        Move the body and slide along collisions.
        Returns the remaining velocity after collisions.
        """
        print(f"[KINEMATIC] move_and_slide called with velocity: {velocity}, floor_normal: {floor_normal}")

        self._velocity = velocity.copy()

        # Update emergency escape cooldown
        if self._emergency_escape_cooldown > 0:
            self._emergency_escape_cooldown -= 1.0/60.0  # Decrease by frame time

        # Get physics world from scene
        physics_world = self._get_physics_world()
        if not physics_world:
            print(f"[KINEMATIC] No physics world found, using fallback movement")
            # Fallback to simple movement
            delta_x = velocity[0] * (1.0/60.0)
            delta_y = velocity[1] * (1.0/60.0)
            self.translate(delta_x, delta_y)
            return velocity.copy()

        # Get our physics body by node reference
        physics_body = physics_world.get_body_by_node(self)
        if not physics_body:
            print(f"[KINEMATIC] No physics body found for {self.name}, using fallback movement")
            # Fallback to simple movement if no physics body
            delta_x = velocity[0] * (1.0/60.0)
            delta_y = velocity[1] * (1.0/60.0)
            self.translate(delta_x, delta_y)
            return velocity.copy()

        print(f"[KINEMATIC] Found physics body for {self.name}")

        # Update physics body position to match node position
        physics_body.update_physics_from_node()

        # Calculate movement delta
        delta_time = 1.0 / 60.0
        move_delta = [velocity[0] * delta_time, velocity[1] * delta_time]

        # If movement is very small, just allow it without collision checking
        if abs(move_delta[0]) < 0.1 and abs(move_delta[1]) < 0.1:
            print(f"[KINEMATIC] Very small movement {move_delta}, allowing without collision check")
            self.translate(move_delta[0], move_delta[1])
            physics_body.update_physics_from_node()
            return velocity.copy()

        # Store last motion for emergency escape (only if we're actually moving)
        if abs(move_delta[0]) > 0.01 or abs(move_delta[1]) > 0.01:
            self._last_motion = move_delta.copy()

        print(f"[KINEMATIC] Calling _test_move with delta: {move_delta}")
        # Try to move and check for collisions using shape casting
        collision_result = self._test_move(physics_body, move_delta, physics_world)

        if collision_result:
            # Collision detected
            normal = collision_result['normal']
            collision_point = collision_result['point']
            distance = collision_result['distance']

            # Convert normal to list if it's a tuple (from physics system)
            if isinstance(normal, tuple):
                normal = list(normal)

            # Convert collision_point to list if it's a tuple
            if isinstance(collision_point, tuple):
                collision_point = list(collision_point)

            print(f"[KINEMATIC] Collision: normal={normal}, point={collision_point}, distance={distance}")

            # Update collision state based on normal direction
            self._update_collision_state(normal)

            # Calculate slide velocity - remove the component of velocity in the collision normal direction
            # This allows perpendicular movement while blocking movement into the collision
            dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]

            # Only block movement if we're moving INTO the collision (dot_product < 0)
            # Positive dot product means moving away from collision (same direction as normal)
            # Negative dot product means moving into collision (opposite direction to normal)
            if dot_product < -0.001:
                print(f"[KINEMATIC] Collision blocking movement: dot_product={dot_product:.3f}")

                # Calculate slide velocity by removing the normal component
                slide_velocity = [
                    velocity[0] - dot_product * normal[0],
                    velocity[1] - dot_product * normal[1]
                ]

                print(f"[KINEMATIC] Original velocity: {velocity}, Slide velocity: {slide_velocity}")

                # Apply slide movement - this allows perpendicular movement
                slide_delta = [slide_velocity[0] * (1.0/60.0), slide_velocity[1] * (1.0/60.0)]

                # Only apply slide movement if it's significant
                if abs(slide_delta[0]) > 0.01 or abs(slide_delta[1]) > 0.01:
                    print(f"[KINEMATIC] Applying slide movement: {slide_delta}")
                    self.translate(slide_delta[0], slide_delta[1])
                    physics_body.update_physics_from_node()
                    return slide_velocity
                else:
                    print(f"[KINEMATIC] No significant slide movement, stopping")
                    physics_body.update_physics_from_node()
                    return [0.0, 0.0]
            else:
                print(f"[KINEMATIC] Collision detected but not blocking movement (dot_product={dot_product:.3f})")
                # We're moving away from the collision (positive dot product) or parallel to it, allow full movement
                self.translate(move_delta[0], move_delta[1])
                physics_body.update_physics_from_node()
                return velocity

        else:
            # No collision, move freely
            self.translate(move_delta[0], move_delta[1])
            # Update physics body position after movement
            physics_body.update_physics_from_node()

            # Clear collision state when no collision occurs
            self._clear_collision_state()

            return velocity.copy()

    def _test_move(self, physics_body, move_delta, physics_world):
        """Test movement and return collision info if collision would occur"""
        # Get current position
        current_pos = physics_body.pymunk_body.position
        target_pos = (current_pos[0] + move_delta[0], current_pos[1] + move_delta[1])

        print(f"[KINEMATIC] Testing move from {current_pos} to {target_pos}, delta: {move_delta}")

        # Get the collision shape size for shape casting
        shape_size = (32.0, 32.0)  # Default size, should get from actual collision shape
        if physics_body.pymunk_shapes:
            # Try to get size from the first collision shape
            shape = physics_body.pymunk_shapes[0]
            if hasattr(shape, 'get_vertices'):
                vertices = shape.get_vertices()
                if vertices:
                    # Calculate bounding box
                    min_x = min(v.x for v in vertices)
                    max_x = max(v.x for v in vertices)
                    min_y = min(v.y for v in vertices)
                    max_y = max(v.y for v in vertices)
                    shape_size = (abs(max_x - min_x), abs(max_y - min_y))
                    print(f"[KINEMATIC] Using shape size: {shape_size}")
            elif hasattr(shape, 'radius'):
                # Circle shape
                radius = shape.radius
                shape_size = (radius * 2, radius * 2)
                print(f"[KINEMATIC] Using circle shape size: {shape_size}")

        # Log shape size for debugging but don't override - collision shapes can be legitimately large
        print(f"[KINEMATIC] Using collision shape size: {shape_size}")

        # Special case: if we're only moving horizontally and the movement is small,
        # start the shape cast from a slightly offset position to avoid immediate overlap detection
        start_pos = current_pos
        if abs(move_delta[1]) < 1.0 and abs(move_delta[0]) > 0.1:
            # For horizontal movement, start the cast from slightly above current position
            start_pos = (current_pos[0], current_pos[1] - 2.0)
            target_pos = (start_pos[0] + move_delta[0], start_pos[1])
            print(f"[KINEMATIC] Horizontal movement detected, using offset start: {start_pos}")

        # Use shape cast instead of simple raycast to account for body size
        # Exclude our own physics body from collision detection
        hit = physics_world.shape_cast(
            "rectangle",
            shape_size,
            start_pos,
            target_pos,
            collision_mask=self.collision_mask,
            exclude_body=physics_body
        )

        if hit:
            print(f"[KINEMATIC] Shape cast hit detected: {hit}")
            return {
                'distance': hit['distance'],
                'normal': hit['normal'],
                'point': hit['point'],
                'body': hit['body']
            }
        else:
            print(f"[KINEMATIC] No shape cast hit detected")

        return None

    def _get_physics_world(self):
        """Get the physics world from the game engine"""
        try:
            # Try to get physics world from global game engine
            from core.game_engine import get_global_game_engine
            game_engine = get_global_game_engine()
            print(f"[KINEMATIC] Game engine: {game_engine}")

            if game_engine:
                # Try multiple access patterns for physics world
                physics_world = None

                # Method 1: Direct access to physics_world
                if hasattr(game_engine, 'physics_world') and game_engine.physics_world:
                    physics_world = game_engine.physics_world
                    print(f"[KINEMATIC] Found physics_world directly: {physics_world}")

                # Method 2: Through systems.physics_world
                elif hasattr(game_engine, 'systems') and hasattr(game_engine.systems, 'physics_world') and game_engine.systems.physics_world:
                    physics_world = game_engine.systems.physics_world
                    print(f"[KINEMATIC] Found physics_world in systems: {physics_world}")

                if physics_world:
                    return physics_world
                else:
                    print(f"[KINEMATIC] No physics_world found in game engine")
            else:
                print(f"[KINEMATIC] No global game engine found")

        except Exception as e:
            print(f"[KINEMATIC] Exception getting physics world from game engine: {e}")
            import traceback
            traceback.print_exc()

        return None

    def _get_shape_size(self, physics_body):
        """Get the size of the physics body's collision shape"""
        shape_size = (32.0, 32.0)  # Default size
        if physics_body and physics_body.pymunk_shapes:
            shape = physics_body.pymunk_shapes[0]
            if hasattr(shape, 'get_vertices'):
                vertices = shape.get_vertices()
                if vertices:
                    min_x = min(v.x for v in vertices)
                    max_x = max(v.x for v in vertices)
                    min_y = min(v.y for v in vertices)
                    max_y = max(v.y for v in vertices)
                    shape_size = (abs(max_x - min_x), abs(max_y - min_y))
            elif hasattr(shape, 'radius'):
                # Circle shape
                radius = shape.radius
                shape_size = (radius * 2, radius * 2)

        # Log shape size for debugging but don't override - collision shapes can be legitimately large
        print(f"[KINEMATIC] _get_shape_size returning: {shape_size}")

        return shape_size

    def _emergency_escape(self, physics_body, physics_world):
        """Emergency escape mechanism - move backwards from last motion with small distance"""
        print(f"[KINEMATIC] Executing emergency escape")

        current_pos = physics_body.pymunk_body.position
        original_node_pos = self.position.copy()
        shape_size = self._get_shape_size(physics_body)

        print(f"[KINEMATIC] Emergency escape: current_pos={current_pos}, node_pos={original_node_pos}")
        print(f"[KINEMATIC] Last motion was: {self._last_motion}")

        # First try: move backwards from last motion (inverse direction)
        if abs(self._last_motion[0]) > 0.01 or abs(self._last_motion[1]) > 0.01:
            # Move backwards with smaller distance
            backwards_distance = min(max(shape_size[0], shape_size[1]) * 0.1, 10.0)  # Very small movement
            backwards_move = [
                -self._last_motion[0] / max(abs(self._last_motion[0]), abs(self._last_motion[1])) * backwards_distance,
                -self._last_motion[1] / max(abs(self._last_motion[0]), abs(self._last_motion[1])) * backwards_distance
            ]

            print(f"[KINEMATIC] Trying backwards escape: {backwards_move}")
            test_result = self._test_move(physics_body, backwards_move, physics_world)
            if not test_result:
                self.translate(backwards_move[0], backwards_move[1])
                print(f"[KINEMATIC] Backwards emergency escape successful: moved {backwards_move}")
                return

        # Second try: small movements in cardinal directions
        escape_distance = min(max(shape_size[0], shape_size[1]) * 0.05, 5.0)  # Even smaller
        directions = [
            [0.0, -escape_distance],   # Up
            [0.0, escape_distance],    # Down
            [-escape_distance, 0.0],   # Left
            [escape_distance, 0.0],    # Right
        ]

        for direction in directions:
            test_result = self._test_move(physics_body, direction, physics_world)
            if not test_result:
                self.translate(direction[0], direction[1])
                print(f"[KINEMATIC] Cardinal direction escape successful: moved {direction}")
                return

        # Final fallback: tiny upward movement
        emergency_move = [0.0, -escape_distance]
        self.translate(emergency_move[0], emergency_move[1])
        print(f"[KINEMATIC] Emergency escape fallback: moved {emergency_move} from {original_node_pos} to {self.position}")

    def _update_collision_state(self, normal: List[float]):
        """Update collision state based on collision normal"""
        import time
        current_time = time.time()

        # Ensure normal is a list (convert from tuple if needed)
        if isinstance(normal, tuple):
            normal = list(normal)

        # Convert floor_max_angle from degrees to radians for calculation
        import math
        max_angle_rad = math.radians(self.floor_max_angle)

        # Calculate angle between normal and up vector [0, -1]
        # normal[1] > 0 means normal points up (floor)
        # normal[1] < 0 means normal points down (ceiling)
        # abs(normal[0]) > abs(normal[1]) means more horizontal (wall)

        if normal[1] > math.cos(max_angle_rad):  # Floor collision
            self._collision_state['on_floor'] = True
            self._collision_state['floor_normal'] = normal.copy()
            self._collision_state['last_floor_time'] = current_time
            print(f"[KINEMATIC] Floor collision detected: normal={normal}")
        elif normal[1] < -math.cos(max_angle_rad):  # Ceiling collision
            self._collision_state['on_ceiling'] = True
            self._collision_state['ceiling_normal'] = normal.copy()
            self._collision_state['last_ceiling_time'] = current_time
            print(f"[KINEMATIC] Ceiling collision detected: normal={normal}")
        else:  # Wall collision (more horizontal than vertical)
            self._collision_state['on_wall'] = True
            self._collision_state['wall_normal'] = normal.copy()
            self._collision_state['last_wall_time'] = current_time
            print(f"[KINEMATIC] Wall collision detected: normal={normal}")

    def _clear_collision_state(self):
        """Clear collision state when no collision occurs"""
        import time
        current_time = time.time()

        # Only clear collision states if they're old enough (coyote time)
        coyote_time = 0.1  # 100ms coyote time

        if current_time - self._collision_state.get('last_floor_time', 0) > coyote_time:
            self._collision_state['on_floor'] = False
        if current_time - self._collision_state.get('last_wall_time', 0) > coyote_time:
            self._collision_state['on_wall'] = False
        if current_time - self._collision_state.get('last_ceiling_time', 0) > coyote_time:
            self._collision_state['on_ceiling'] = False

    def _check_collision_along_path(self, move_delta: List[float], physics_world) -> Optional[Dict[str, Any]]:
        """Check for collisions along movement path using shape cast for better accuracy"""
        if not physics_world:
            return None

        # Get our physics body to exclude it from collision detection
        physics_body = physics_world.get_body_by_node(self)

        # Calculate start and end points
        start_pos = self.position.copy()
        end_pos = [start_pos[0] + move_delta[0], start_pos[1] + move_delta[1]]

        # Get collision shape size for accurate shape casting
        shape_size = (32.0, 32.0)  # Default size
        if physics_body and physics_body.pymunk_shapes:
            shape = physics_body.pymunk_shapes[0]
            if hasattr(shape, 'get_vertices'):
                vertices = shape.get_vertices()
                if vertices:
                    min_x = min(v.x for v in vertices)
                    max_x = max(v.x for v in vertices)
                    min_y = min(v.y for v in vertices)
                    max_y = max(v.y for v in vertices)
                    shape_size = (max_x - min_x, max_y - min_y)
            elif hasattr(shape, 'radius'):
                # Circle shape
                radius = shape.radius
                shape_size = (radius, radius)

        # Use shape cast for more accurate collision detection
        hit_info = physics_world.shape_cast(
            "rectangle",
            shape_size,
            (start_pos[0], start_pos[1]),
            (end_pos[0], end_pos[1]),
            collision_mask=self.collision_mask,
            exclude_body=physics_body
        )

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
        return self._collision_state['on_floor']

    def is_on_wall(self) -> bool:
        """Check if the body is touching a wall"""
        return self._collision_state['on_wall']

    def is_on_ceiling(self) -> bool:
        """Check if the body is touching the ceiling"""
        return self._collision_state['on_ceiling']

    def get_floor_normal(self) -> List[float]:
        """Get the normal vector of the floor surface"""
        return self._collision_state['floor_normal'].copy()

    def get_wall_normal(self) -> List[float]:
        """Get the normal vector of the wall surface"""
        return self._collision_state['wall_normal'].copy()

    def get_ceiling_normal(self) -> List[float]:
        """Get the normal vector of the ceiling surface"""
        return self._collision_state['ceiling_normal'].copy()

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
            "_velocity": self._velocity.copy(),
            "_collision_state": self._collision_state.copy()
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

        # Restore collision state if available
        if "_collision_state" in data:
            body._collision_state = data["_collision_state"].copy()
        else:
            # Initialize default collision state if not in data
            body._collision_state = {
                'on_floor': False,
                'on_wall': False,
                'on_ceiling': False,
                'floor_normal': [0.0, 1.0],  # Floor normal points UP (correct)
                'wall_normal': [1.0, 0.0],
                'ceiling_normal': [0.0, -1.0],  # Ceiling normal points DOWN (correct)
                'last_floor_time': 0.0,
                'last_wall_time': 0.0,
                'last_ceiling_time': 0.0
            }

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
