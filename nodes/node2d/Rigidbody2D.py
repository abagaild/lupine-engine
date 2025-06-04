"""
RigidBody2D node implementation for Lupine Engine
Physics-driven body (Rigid, Static, Kinematic, Character modes)
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class RigidBody2D(Node2D):
    """
    RigidBody2D: A fully physics-driven body.
    Choose from modes: Rigid, Static, Kinematic (controlled), or Character.
    """

    def __init__(self, name: str = "RigidBody2D"):
        super().__init__(name)
        self.type = "RigidBody2D"

        # Export variables for editor
        self.export_variables = {
            "mode": {
                "type": "enum",
                "value": "Rigid",
                "options": ["Rigid", "Static", "Kinematic", "Character"],
                "description": "Physics mode"
            },
            "mass": {
                "type": "float",
                "value": 1.0,
                "min": 0.001,
                "description": "Mass of the body"
            },
            "friction": {
                "type": "float",
                "value": 0.5,
                "description": "Surface friction coefficient"
            },
            "bounce": {
                "type": "float",
                "value": 0.0,
                "description": "Restitution (0 = no bounce, 1 = perfect bounce)"
            },
            "gravity_scale": {
                "type": "float",
                "value": 1.0,
                "description": "Multiplier on global gravity"
            },
            "linear_velocity": {
                "type": "vector2",
                "value": [0.0, 0.0],
                "description": "Initial or desired linear velocity"
            },
            "angular_velocity": {
                "type": "float",
                "value": 0.0,
                "description": "Initial angular speed"
            },
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
            "can_sleep": {
                "type": "bool",
                "value": True,
                "description": "Allow body to sleep when idle"
            },
            "sleep_borders": {
                "type": "float",
                "value": 0.1,
                "description": "Threshold for entering sleep"
            },
            "continuous_cd": {
                "type": "bool",
                "value": False,
                "description": "Continuous collision detection"
            }
        }

        # Core properties
        self.mode: str = "Rigid"
        self.mass: float = 1.0
        self.friction: float = 0.5
        self.bounce: float = 0.0
        self.gravity_scale: float = 1.0
        self.linear_velocity: List[float] = [0.0, 0.0]
        self.angular_velocity: float = 0.0
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self.can_sleep: bool = True
        self.sleep_borders: float = 0.1
        self.continuous_cd: bool = False

        # Internal physics state (stubbed)
        self._is_sleeping: bool = False
        self._force_accumulator: List[float] = [0.0, 0.0]
        self._torque_accumulator: float = 0.0

        # Built-in signals
        self.add_signal("body_entered")
        self.add_signal("body_exited")
        self.add_signal("sleeping")
        self.add_signal("woke_up")

    def apply_force(self, force: List[float]):
        """Apply a linear force to the body (stubbed)."""
        # In real physics, accumulate and integrate
        self._force_accumulator[0] += force[0]
        self._force_accumulator[1] += force[1]

    def apply_torque(self, torque: float):
        """Apply a torque to the body (stubbed)."""
        self._torque_accumulator += torque

    def apply_impulse(self, impulse: List[float], position: Optional[List[float]] = None):
        """Apply an impulse to the body"""
        if position is None:
            position = [0.0, 0.0]  # Apply at center of mass

        # Add to force accumulator for physics system to process
        self._force_accumulator[0] += impulse[0]
        self._force_accumulator[1] += impulse[1]

        # Wake up the body if sleeping
        if self._is_sleeping:
            self.wake_up()

    def set_linear_velocity(self, velocity: List[float]):
        """Set the linear velocity of the body"""
        self.linear_velocity = velocity.copy()

        # Wake up the body if sleeping
        if self._is_sleeping:
            self.wake_up()

    def get_linear_velocity(self) -> List[float]:
        """Get the current linear velocity"""
        return self.linear_velocity.copy()

    def set_angular_velocity(self, velocity: float):
        """Set the angular velocity of the body"""
        self.angular_velocity = velocity

        # Wake up the body if sleeping
        if self._is_sleeping:
            self.wake_up()

    def get_angular_velocity(self) -> float:
        """Get the current angular velocity"""
        return self.angular_velocity

    def sleep(self):
        """Put the body to sleep"""
        if self.can_sleep and not self._is_sleeping:
            self._is_sleeping = True
            self.linear_velocity = [0.0, 0.0]
            self.angular_velocity = 0.0
            self.emit_signal("sleeping")

    def wake_up(self):
        """Wake up the body"""
        if self._is_sleeping:
            self._is_sleeping = False
            self.emit_signal("woke_up")

    def is_sleeping(self) -> bool:
        """Check if the body is sleeping"""
        return self._is_sleeping

    def get_colliding_bodies(self) -> List['Node2D']:
        """Get list of bodies currently colliding with this one"""
        # This would be populated by the physics system
        return []

    def set_mode(self, mode: str):
        """Set the physics mode of the body"""
        valid_modes = ["Rigid", "Static", "Kinematic", "Character"]
        if mode in valid_modes:
            self.mode = mode
        else:
            print(f"Warning: Invalid RigidBody2D mode '{mode}'. Valid modes: {valid_modes}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize RigidBody2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "mode": self.mode,
            "mass": self.mass,
            "friction": self.friction,
            "bounce": self.bounce,
            "gravity_scale": self.gravity_scale,
            "linear_velocity": self.linear_velocity.copy(),
            "angular_velocity": self.angular_velocity,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "can_sleep": self.can_sleep,
            "sleep_borders": self.sleep_borders,
            "continuous_cd": self.continuous_cd,
            "_is_sleeping": self._is_sleeping,
            "_force_accumulator": self._force_accumulator.copy(),
            "_torque_accumulator": self._torque_accumulator
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RigidBody2D":
        """Deserialize a RigidBody2D from a dictionary."""
        body = cls(data.get("name", "RigidBody2D"))
        cls._apply_node_properties(body, data)

        body.mode = data.get("mode", "Rigid")
        body.mass = data.get("mass", 1.0)
        body.friction = data.get("friction", 0.5)
        body.bounce = data.get("bounce", 0.0)
        body.gravity_scale = data.get("gravity_scale", 1.0)
        body.linear_velocity = data.get("linear_velocity", [0.0, 0.0])
        body.angular_velocity = data.get("angular_velocity", 0.0)
        body.collision_layer = data.get("collision_layer", 1)
        body.collision_mask = data.get("collision_mask", 1)
        body.can_sleep = data.get("can_sleep", True)
        body.sleep_borders = data.get("sleep_borders", 0.1)
        body.continuous_cd = data.get("continuous_cd", False)
        body._is_sleeping = data.get("_is_sleeping", False)
        body._force_accumulator = data.get("_force_accumulator", [0.0, 0.0])
        body._torque_accumulator = data.get("_torque_accumulator", 0.0)

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            body.add_child(child)
        return body
