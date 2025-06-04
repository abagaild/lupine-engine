"""
Platformer Player Controller for Lupine Engine
A kinematic body player controller for side-scrolling platformer games
"""

from nodes.node2d.KinematicBody2D import KinematicBody2D
from typing import Dict, Any, List, Optional
import math


class PlatformerPlayerController(KinematicBody2D):
    """
    Platformer Player Controller: A kinematic body for side-scrolling platformer games.
    
    Features:
    - Horizontal movement with acceleration and friction
    - Gravity and jumping mechanics
    - Coyote time and jump buffering
    - Variable jump height
    - Expects child CollisionShape2D for main collision
    - Expects child Area2D with CollisionShape2D for interaction detection
    - Expects child Sprite or AnimatedSprite for visual representation
    - Input action-based movement system
    """

    def __init__(self, name: str = "PlatformerPlayerController"):
        super().__init__(name)
        self.type = "PlatformerPlayerController"

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
                "description": "Horizontal movement speed in pixels per second"
            },
            "acceleration": {
                "type": "float",
                "value": 800.0,
                "min": 0.0,
                "max": 5000.0,
                "step": 50.0,
                "description": "Horizontal acceleration when starting to move"
            },
            "friction": {
                "type": "float",
                "value": 800.0,
                "min": 0.0,
                "max": 5000.0,
                "step": 50.0,
                "description": "Horizontal deceleration when stopping"
            },
            "jump_height": {
                "type": "float",
                "value": 100.0,
                "min": 0.0,
                "max": 500.0,
                "step": 10.0,
                "description": "Maximum jump height in pixels"
            },
            "jump_time_to_peak": {
                "type": "float",
                "value": 0.4,
                "min": 0.1,
                "max": 2.0,
                "step": 0.05,
                "description": "Time to reach jump peak in seconds"
            },
            "jump_time_to_descent": {
                "type": "float",
                "value": 0.3,
                "min": 0.1,
                "max": 2.0,
                "step": 0.05,
                "description": "Time to fall from peak in seconds"
            },
            "coyote_time": {
                "type": "float",
                "value": 0.1,
                "min": 0.0,
                "max": 0.5,
                "step": 0.01,
                "description": "Grace period for jumping after leaving ground"
            },
            "jump_buffer_time": {
                "type": "float",
                "value": 0.1,
                "min": 0.0,
                "max": 0.5,
                "step": 0.01,
                "description": "Buffer time for jump input before landing"
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
        self.jump_height: float = 100.0
        self.jump_time_to_peak: float = 0.4
        self.jump_time_to_descent: float = 0.3
        self.coyote_time: float = 0.1
        self.jump_buffer_time: float = 0.1
        self.input_enabled: bool = True

        # Calculated jump physics
        self._jump_velocity: float = 0.0
        self._jump_gravity: float = 0.0
        self._fall_gravity: float = 0.0
        self._calculate_jump_physics()

        # Internal movement state
        self._velocity: List[float] = [0.0, 0.0]
        self._input_vector: List[float] = [0.0, 0.0]
        self._is_on_floor: bool = False
        self._was_on_floor: bool = False
        self._coyote_timer: float = 0.0
        self._jump_buffer_timer: float = 0.0
        self._jump_held: bool = False

        # Child node references (set during _ready)
        self._collision_shape: Optional[Any] = None
        self._interaction_area: Optional[Any] = None
        self._sprite: Optional[Any] = None
        self._is_action_pressed_func: Optional[Any] = None

        # Built-in signals
        self.add_signal("moved")
        self.add_signal("stopped")
        self.add_signal("jumped")
        self.add_signal("landed")
        self.add_signal("direction_changed")

    def _calculate_jump_physics(self):
        """Calculate jump velocity and gravity from jump height and timing"""
        # Calculate jump velocity and gravity using kinematic equations
        # v = gt, h = vt - 0.5gt²
        self._jump_velocity = (2.0 * self.jump_height) / self.jump_time_to_peak
        self._jump_gravity = (2.0 * self.jump_height) / (self.jump_time_to_peak * self.jump_time_to_peak)
        self._fall_gravity = (2.0 * self.jump_height) / (self.jump_time_to_descent * self.jump_time_to_descent)

    def _ready(self):
        """Called when the node enters the scene tree"""
        super()._ready()
        print(f"[DEBUG] PlatformerPlayerController._ready() called for {self.name}")
        self._find_child_nodes()

        # Get the input function from the global game engine instance
        try:
            from core.game_engine import get_global_game_engine
            game_engine = get_global_game_engine()
            if game_engine and hasattr(game_engine, 'is_action_pressed'):
                self._is_action_pressed_func = game_engine.is_action_pressed
                print(f"[DEBUG] PlatformerPlayerController: Found is_action_pressed in game engine")
            else:
                print(f"[PlatformerPlayerController] Warning: 'is_action_pressed' not found in game engine for {self.name}")
        except Exception as e:
            print(f"[PlatformerPlayerController] Error getting 'is_action_pressed' from game engine: {e}")

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

        # Update floor detection
        self._was_on_floor = self._is_on_floor
        self._is_on_floor = self.is_on_floor()

        # Handle landing
        if self._is_on_floor and not self._was_on_floor:
            self.emit_signal("landed")

        # Update timers
        self._update_timers(delta)

        # Get input vector
        self._update_input_vector()
        
        # Apply horizontal movement
        self._apply_horizontal_movement(delta)
        
        # Apply vertical movement (gravity and jumping)
        self._apply_vertical_movement(delta)
        
        # Move the character
        self._move_character(delta)

    def _update_timers(self, delta: float):
        """Update coyote time and jump buffer timers"""
        # Coyote time - grace period for jumping after leaving ground
        if self._is_on_floor:
            self._coyote_timer = self.coyote_time
        else:
            self._coyote_timer = max(0.0, self._coyote_timer - delta)

        # Jump buffer - buffer jump input before landing
        if self._jump_buffer_timer > 0.0:
            self._jump_buffer_timer = max(0.0, self._jump_buffer_timer - delta)

    def _update_input_vector(self):
        """Update input vector based on action inputs"""
        try:
            # Get input from action system
            input_x = 0.0
            jump_pressed = False
            
            # Use the stored input function if available
            if self._is_action_pressed_func:
                if self._is_action_pressed_func("move_left"):
                    input_x -= 1.0
                if self._is_action_pressed_func("move_right"):
                    input_x += 1.0

                # Jump input handling
                if self._is_action_pressed_func("jump"):
                    if not self._jump_held:
                        # Jump was just pressed
                        self._jump_buffer_timer = self.jump_buffer_time
                    jump_pressed = True
            else:
                # Fallback - input will remain 0,0
                pass
                
            # Store previous input for direction change detection
            previous_input = self._input_vector.copy()
            self._input_vector = [input_x, 0.0]  # Y is handled by gravity/jumping
            self._jump_held = jump_pressed
            
            # Emit direction changed signal if horizontal input changed
            if previous_input[0] != self._input_vector[0]:
                self.emit_signal("direction_changed", self._input_vector.copy())
                
        except Exception as e:
            print(f"[PlatformerPlayerController] Input error: {e}")
            self._input_vector = [0.0, 0.0]
            self._jump_held = False

    def _apply_horizontal_movement(self, delta: float):
        """Apply horizontal acceleration and friction"""
        target_velocity_x = self._input_vector[0] * self.speed
        
        if abs(target_velocity_x) > 0.1:
            # Accelerate towards target velocity
            if abs(self._velocity[0]) < abs(target_velocity_x):
                self._velocity[0] = self._move_toward(
                    self._velocity[0], 
                    target_velocity_x, 
                    self.acceleration * delta
                )
            else:
                self._velocity[0] = target_velocity_x
        else:
            # Apply friction
            self._velocity[0] = self._move_toward(
                self._velocity[0], 
                0.0, 
                self.friction * delta
            )

    def _apply_vertical_movement(self, delta: float):
        """Apply gravity and jumping"""
        # Handle jumping
        if self._jump_buffer_timer > 0.0 and self._coyote_timer > 0.0:
            # Perform jump
            self._velocity[1] = self._jump_velocity  # Positive Y is up
            self._jump_buffer_timer = 0.0
            self._coyote_timer = 0.0
            self.emit_signal("jumped")

        # Apply gravity
        if not self._is_on_floor:
            # Use different gravity for rising vs falling
            if self._velocity[1] > 0 and self._jump_held:
                # Rising and jump held - use jump gravity
                self._velocity[1] -= self._jump_gravity * delta
            else:
                # Falling or jump released - use fall gravity
                self._velocity[1] -= self._fall_gravity * delta

    def _move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move a value toward a target by a maximum amount"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def _move_character(self, delta: float):
        """Move the character using move_and_slide"""
        # delta parameter kept for consistency with physics processing
        # Store previous position for movement detection
        previous_pos = self.position.copy()
        
        # Use move_and_slide for collision handling
        self.move_and_slide(self._velocity, [0.0, 1.0])  # Down vector for floor detection
        
        # Check if actually moved
        if previous_pos != self.position:
            self.emit_signal("moved", self.position.copy())
        elif abs(self._velocity[0]) <= 0.1 and self._is_on_floor:
            # Emit stopped signal when horizontal velocity is near zero and on floor
            self.emit_signal("stopped")

    def set_speed(self, new_speed: float):
        """Set horizontal movement speed"""
        self.speed = max(0.0, new_speed)

    def set_acceleration(self, new_acceleration: float):
        """Set horizontal acceleration"""
        self.acceleration = max(0.0, new_acceleration)

    def set_friction(self, new_friction: float):
        """Set horizontal friction"""
        self.friction = max(0.0, new_friction)

    def set_jump_height(self, new_height: float):
        """Set jump height and recalculate jump physics"""
        self.jump_height = max(0.0, new_height)
        self._calculate_jump_physics()

    def set_jump_timing(self, time_to_peak: float, time_to_descent: float):
        """Set jump timing and recalculate jump physics"""
        self.jump_time_to_peak = max(0.1, time_to_peak)
        self.jump_time_to_descent = max(0.1, time_to_descent)
        self._calculate_jump_physics()

    def get_velocity(self) -> List[float]:
        """Get current velocity"""
        return self._velocity.copy()

    def set_velocity(self, velocity: List[float]):
        """Set velocity directly"""
        self._velocity = velocity.copy()

    def get_input_vector(self) -> List[float]:
        """Get current input vector"""
        return self._input_vector.copy()

    def is_on_floor(self) -> bool:
        """Check if the character is on the floor"""
        # This would be implemented by the KinematicBody2D's move_and_slide
        # For now, return a simple check
        return getattr(self, '_on_floor', False)

    def is_jumping(self) -> bool:
        """Check if the character is currently jumping (moving upward)"""
        return self._velocity[1] > 10.0  # Positive Y is up

    def is_falling(self) -> bool:
        """Check if the character is currently falling (moving downward)"""
        return self._velocity[1] < -10.0 and not self._is_on_floor

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
        """Serialize PlatformerPlayerController to a dictionary"""
        data = super().to_dict()
        data.update({
            "speed": self.speed,
            "acceleration": self.acceleration,
            "friction": self.friction,
            "jump_height": self.jump_height,
            "jump_time_to_peak": self.jump_time_to_peak,
            "jump_time_to_descent": self.jump_time_to_descent,
            "coyote_time": self.coyote_time,
            "jump_buffer_time": self.jump_buffer_time,
            "input_enabled": self.input_enabled,
            "_velocity": self._velocity.copy(),
            "_input_vector": self._input_vector.copy(),
            "_is_on_floor": self._is_on_floor,
            "_coyote_timer": self._coyote_timer,
            "_jump_buffer_timer": self._jump_buffer_timer,
            "_jump_held": self._jump_held
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlatformerPlayerController":
        """Deserialize a PlatformerPlayerController from a dictionary"""
        controller = cls(data.get("name", "PlatformerPlayerController"))

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

        # Apply PlatformerPlayerController specific properties
        controller.speed = data.get("speed", 200.0)
        controller.acceleration = data.get("acceleration", 800.0)
        controller.jump_height = data.get("jump_height", 100.0)
        controller.jump_time_to_peak = data.get("jump_time_to_peak", 0.4)
        controller.jump_time_to_descent = data.get("jump_time_to_descent", 0.3)
        controller.coyote_time = data.get("coyote_time", 0.1)
        controller.jump_buffer_time = data.get("jump_buffer_time", 0.1)
        controller.input_enabled = data.get("input_enabled", True)
        controller._velocity = data.get("_velocity", [0.0, 0.0]).copy()
        controller._input_vector = data.get("_input_vector", [0.0, 0.0]).copy()
        controller._is_on_floor = data.get("_is_on_floor", False)
        controller._coyote_timer = data.get("_coyote_timer", 0.0)
        controller._jump_buffer_timer = data.get("_jump_buffer_timer", 0.0)
        controller._jump_held = data.get("_jump_held", False)

        # Recalculate jump physics
        controller._calculate_jump_physics()

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
