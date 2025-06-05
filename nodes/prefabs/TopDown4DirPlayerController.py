"""
TopDown 4-Direction Player Controller for Lupine Engine
A kinematic body player controller for top-down games with 4-directional movement
"""

from nodes.node2d.KinematicBody2D import KinematicBody2D
from typing import Dict, Any, List, Optional
import math


class TopDown4DirPlayerController(KinematicBody2D):
    """
    TopDown 4-Direction Player Controller: A kinematic body for top-down games.
    
    Features:
    - 4-directional movement (up, down, left, right)
    - Configurable speed and acceleration
    - Expects child CollisionShape2D for main collision
    - Expects child Area2D with CollisionShape2D for interaction detection
    - Expects child Sprite or AnimatedSprite for visual representation
    - Input action-based movement system
    """

    def __init__(self, name: str = "TopDown4DirPlayerController"):
        super().__init__(name)
        self.type = "TopDown4DirPlayerController"

        # Ensure physics system recognizes this as a kinematic body
        self.physics_body_type = "kinematic"

        # Export variables for editor
        self.export_variables.update({
            "speed": {
                "type": "float",
                "value": 200.0,
                "min": 0.0,
                "max": 1000.0,
                "step": 10.0,
                "description": "Movement speed in pixels per second"
            },
            "acceleration": {
                "type": "float",
                "value": 800.0,
                "min": 0.0,
                "max": 5000.0,
                "step": 50.0,
                "description": "Acceleration when starting to move"
            },
            "friction": {
                "type": "float",
                "value": 800.0,
                "min": 0.0,
                "max": 5000.0,
                "step": 50.0,
                "description": "Deceleration when stopping"
            },
            "input_enabled": {
                "type": "bool",
                "value": True,
                "description": "Enable input processing"
            }
        })

        # Movement properties
        self.speed: float = 200.0
        self.acceleration: float = 800.0
        self.friction: float = 800.0
        self.input_enabled: bool = True

        # Internal movement state
        self._velocity: List[float] = [0.0, 0.0]
        self._input_vector: List[float] = [0.0, 0.0]

        # Child node references (set during _ready)
        self._collision_shape: Optional[Any] = None
        self._interaction_area: Optional[Any] = None
        self._sprite: Optional[Any] = None
        self._is_action_pressed_func: Optional[Any] = None

        # Built-in signals
        self.add_signal("moved")
        self.add_signal("stopped")
        self.add_signal("direction_changed")

    def _ready(self):
        """Called when the node enters the scene tree"""
        super()._ready()
        print(f"[DEBUG] TopDown4DirPlayerController._ready() called for {self.name}")
        self._find_child_nodes()

        # Get the input function from the global game engine instance
        try:
            from core.game_engine import get_global_game_engine
            game_engine = get_global_game_engine()
            if game_engine and hasattr(game_engine, 'is_action_pressed'):
                self._is_action_pressed_func = game_engine.is_action_pressed
                print(f"[DEBUG] TopDown4DirPlayerController: Found is_action_pressed in game engine")
            else:
                print(f"[TopDown4DirPlayerController] Warning: 'is_action_pressed' not found in game engine for {self.name}")
        except Exception as e:
            print(f"[TopDown4DirPlayerController] Error getting 'is_action_pressed' from game engine: {e}")

    def _find_child_nodes(self):
        """Find and cache references to expected child nodes"""
        for child in self.children:
            if hasattr(child, 'type'):
                if child.type == "CollisionShape2D" and self._collision_shape is None:
                    self._collision_shape = child
                elif child.type == "Area2D" and self._interaction_area is None:
                    self._interaction_area = child
                elif child.type in ["Sprite", "AnimatedSprite"] and self._sprite is None:
                    self._sprite = child

        # Warn if expected children are missing
        if self._collision_shape is None:
            print(f"Warning: {self.name} expects a CollisionShape2D child for collision detection")
        if self._interaction_area is None:
            print(f"Warning: {self.name} expects an Area2D child for interaction detection")
        if self._sprite is None:
            print(f"Warning: {self.name} expects a Sprite or AnimatedSprite child for visual representation")

    def _physics_process(self, delta: float):
        """Handle physics processing for movement"""
        super()._physics_process(delta)

        if not self.input_enabled:
            return

        # Debug: Print that physics process is running (only occasionally to avoid spam)
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
        else:
            self._debug_counter = 0

        if self._debug_counter % 60 == 0:  # Print every 60 frames (about once per second)
            print(f"[DEBUG] {self.name} _physics_process running (frame {self._debug_counter})")

        # Get input vector
        self._update_input_vector()

        # Apply movement
        self._apply_movement(delta)

        # Move the character
        self._move_character(delta)

    def _update_input_vector(self):
        """Update input vector based on action inputs"""
        try:
            # Get input from action system
            input_x = 0.0
            input_y = 0.0

            # Use the stored input function if available
            if self._is_action_pressed_func:
                # Debug: Check if any movement keys are pressed
                left_pressed = self._is_action_pressed_func("move_left")
                right_pressed = self._is_action_pressed_func("move_right")
                up_pressed = self._is_action_pressed_func("move_up")
                down_pressed = self._is_action_pressed_func("move_down")

                if left_pressed or right_pressed or up_pressed or down_pressed:
                    print(f"[DEBUG] Input detected - Left: {left_pressed}, Right: {right_pressed}, Up: {up_pressed}, Down: {down_pressed}")

                if left_pressed:
                    input_x -= 1.0
                if right_pressed:
                    input_x += 1.0
                if up_pressed:
                    input_y += 1.0
                if down_pressed:
                    input_y -= 1.0
            else:
                # Fallback - input will remain 0,0
                pass
            
            # Store previous input for direction change detection
            # Handle both list and tuple input vectors safely
            if isinstance(self._input_vector, list):
                previous_input = self._input_vector.copy()
            else:
                previous_input = list(self._input_vector)

            # 4-directional movement - prioritize one axis if both are pressed
            if input_x != 0.0 and input_y != 0.0:
                # Prioritize horizontal movement
                input_y = 0.0

            self._input_vector = [input_x, input_y]

            # Emit direction changed signal if input direction changed
            if previous_input != self._input_vector and (self._input_vector[0] != 0.0 or self._input_vector[1] != 0.0):
                self.emit_signal("direction_changed", self._input_vector.copy())
                
        except Exception as e:
            print(f"[TopDown4DirPlayerController] Input error: {e}")
            self._input_vector = [0.0, 0.0]

    def _apply_movement(self, delta: float):
        """Apply acceleration and friction to velocity"""
        target_velocity = [
            self._input_vector[0] * self.speed,
            self._input_vector[1] * self.speed
        ]
        
        # Apply acceleration or friction
        for i in range(2):
            if abs(target_velocity[i]) > 0.1:
                # Accelerate towards target velocity
                if abs(self._velocity[i]) < abs(target_velocity[i]):
                    self._velocity[i] = self._move_toward(
                        self._velocity[i], 
                        target_velocity[i], 
                        self.acceleration * delta
                    )
                else:
                    self._velocity[i] = target_velocity[i]
            else:
                # Apply friction
                self._velocity[i] = self._move_toward(
                    self._velocity[i], 
                    0.0, 
                    self.friction * delta
                )

    def _move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move a value toward a target by a maximum amount"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def _move_character(self, delta: float):
        """Move the character using move_and_slide"""
        # delta parameter kept for consistency with physics processing
        if abs(self._velocity[0]) > 0.1 or abs(self._velocity[1]) > 0.1:
            # Store previous position for movement detection
            # Handle both list and tuple positions safely
            if isinstance(self.position, list):
                previous_pos = self.position.copy()
            else:
                previous_pos = list(self.position)

            # Use move_and_slide for collision handling
            self.move_and_slide(self._velocity, [0.0, -1.0])  # Up vector for floor detection

            # Check if actually moved
            if previous_pos != list(self.position):
                # Safely get position as list for signal emission
                current_pos = list(self.position) if not isinstance(self.position, list) else self.position.copy()
                self.emit_signal("moved", current_pos)
        else:
            # Emit stopped signal when velocity is near zero
            if abs(self._velocity[0]) <= 0.1 and abs(self._velocity[1]) <= 0.1:
                if self._velocity != [0.0, 0.0]:
                    self._velocity = [0.0, 0.0]
                    self.emit_signal("stopped")

    def set_speed(self, new_speed: float):
        """Set movement speed"""
        self.speed = max(0.0, new_speed)

    def set_acceleration(self, new_acceleration: float):
        """Set acceleration"""
        self.acceleration = max(0.0, new_acceleration)

    def set_friction(self, new_friction: float):
        """Set friction"""
        self.friction = max(0.0, new_friction)

    def get_velocity(self) -> List[float]:
        """Get current velocity"""
        return self._velocity.copy()

    def set_velocity(self, velocity: List[float]):
        """Set velocity directly"""
        self._velocity = velocity.copy()

    def get_input_vector(self) -> List[float]:
        """Get current input vector"""
        return self._input_vector.copy()

    def get_collision_shape(self) -> Optional[Any]:
        """Get the collision shape child node"""
        return self._collision_shape

    def get_interaction_area(self) -> Optional[Any]:
        """Get the interaction area child node"""
        return self._interaction_area

    def get_sprite(self) -> Optional[Any]:
        """Get the sprite child node"""
        return self._sprite

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TopDown4DirPlayerController to a dictionary"""
        data = super().to_dict()
        data.update({
            "speed": self.speed,
            "acceleration": self.acceleration,
            "friction": self.friction,
            "input_enabled": self.input_enabled,
            "_velocity": self._velocity.copy(),
            "_input_vector": self._input_vector.copy()
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopDown4DirPlayerController":
        """Deserialize a TopDown4DirPlayerController from a dictionary"""
        controller = cls(data.get("name", "TopDown4DirPlayerController"))

        # Apply Node2D properties using parent's from_dict logic
        # This ensures position, rotation, scale are properly set
        from nodes.base.Node2D import Node2D
        Node2D._apply_node_properties(controller, data)

        # Apply Node2D specific properties
        controller.position = data.get("position", [0.0, 0.0])
        controller.rotation = data.get("rotation", 0.0)
        controller.scale = data.get("scale", [1.0, 1.0])
        controller.z_index = data.get("z_index", 0)
        controller.z_as_relative = data.get("z_as_relative", True)
        controller.visible = data.get("visible", True)

        # Apply KinematicBody2D specific properties
        controller.collision_layer = data.get("collision_layer", 1)
        controller.collision_mask = data.get("collision_mask", 1)
        controller.floor_max_angle = data.get("floor_max_angle", 45.0)
        controller.max_speed = data.get("max_speed", 200.0)
        controller.gravity_scale = data.get("gravity_scale", 1.0)
        controller.friction = data.get("friction", 0.5)
        controller.bounce = data.get("bounce", 0.0)

        # Apply TopDown4DirPlayerController specific properties
        controller.speed = data.get("speed", 200.0)
        controller.acceleration = data.get("acceleration", 800.0)
        controller.input_enabled = data.get("input_enabled", True)
        controller._velocity = data.get("_velocity", [0.0, 0.0]).copy()
        controller._input_vector = data.get("_input_vector", [0.0, 0.0]).copy()

        # Re-create children
        for child_data in data.get("children", []):
            try:
                from core.scene.scene_manager import Scene
                child = Scene._create_node_from_dict(child_data)
                controller.add_child(child)
            except ImportError:
                from nodes.base.Node import Node
                child = Node.from_dict(child_data)
                controller.add_child(child)

        return controller
