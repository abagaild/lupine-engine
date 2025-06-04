"""
Area2D node implementation for Lupine Engine
Non-solid sensor region for triggers and detection zones
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class Area2D(Node2D):
    """
    Area2D: A detection zone that detects bodies or other areas
    entering/exiting, optionally applies gravity/damping.
    """

    def __init__(self, name: str = "Area2D"):
        super().__init__(name)
        self.type = "Area2D"

        # Export variables for editor
        self.export_variables = {
            "collision_layer": {
                "type": "int",
                "value": 1,
                "description": "Which layer the area occupies"
            },
            "collision_mask": {
                "type": "int",
                "value": 1,
                "description": "Which layers this area monitors"
            },
            "monitoring": {
                "type": "bool",
                "value": True,
                "description": "Whether to detect overlaps"
            },
            "monitorable": {
                "type": "bool",
                "value": True,
                "description": "Whether other areas can detect this one"
            },
            "priority": {
                "type": "int",
                "value": 0,
                "description": "Order in which areas process overlaps"
            },
            "gravity": {
                "type": "float",
                "value": 0.0,
                "description": "Gravity strength inside this area"
            },
            "gravity_vector": {
                "type": "vector2",
                "value": [0.0, 1.0],
                "description": "Direction of gravity inside this area"
            },
            "linear_damp": {
                "type": "float",
                "value": 0.0,
                "description": "Linear damping inside area"
            },
            "angular_damp": {
                "type": "float",
                "value": 0.0,
                "description": "Angular damping inside area"
            }
        }

        # Core properties
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self.monitoring: bool = True
        self.monitorable: bool = True
        self.priority: int = 0
        self.gravity: float = 0.0
        self.gravity_vector: List[float] = [0.0, 1.0]
        self.linear_damp: float = 0.0
        self.angular_damp: float = 0.0

        # Built-in signals
        self.add_signal("body_entered")
        self.add_signal("body_exited")
        self.add_signal("area_entered")
        self.add_signal("area_exited")

        # Internal tracking of overlapping bodies and areas
        self._overlapping_bodies: List['Node2D'] = []
        self._overlapping_areas: List['Area2D'] = []

    def get_overlapping_bodies(self) -> List['Node2D']:
        """Get list of bodies currently overlapping this area"""
        return self._overlapping_bodies.copy()

    def get_overlapping_areas(self) -> List['Area2D']:
        """Get list of areas currently overlapping this area"""
        return self._overlapping_areas.copy()

    def overlaps_body(self, body: 'Node2D') -> bool:
        """Check if a specific body is overlapping this area"""
        return body in self._overlapping_bodies

    def overlaps_area(self, area: 'Area2D') -> bool:
        """Check if a specific area is overlapping this area"""
        return area in self._overlapping_areas

    def _on_body_entered(self, body: 'Node2D'):
        """Internal method called when a body enters the area"""
        if body not in self._overlapping_bodies:
            self._overlapping_bodies.append(body)
            self.emit_signal("body_entered", body)

    def _on_body_exited(self, body: 'Node2D'):
        """Internal method called when a body exits the area"""
        if body in self._overlapping_bodies:
            self._overlapping_bodies.remove(body)
            self.emit_signal("body_exited", body)

    def _on_area_entered(self, area: 'Area2D'):
        """Internal method called when an area enters this area"""
        if area not in self._overlapping_areas:
            self._overlapping_areas.append(area)
            self.emit_signal("area_entered", area)

    def _on_area_exited(self, area: 'Area2D'):
        """Internal method called when an area exits this area"""
        if area in self._overlapping_areas:
            self._overlapping_areas.remove(area)
            self.emit_signal("area_exited", area)

    def set_monitoring(self, enabled: bool):
        """Enable or disable monitoring of overlaps"""
        self.monitoring = enabled

    def is_monitoring(self) -> bool:
        """Check if monitoring is enabled"""
        return self.monitoring

    def set_monitorable(self, enabled: bool):
        """Enable or disable being monitored by other areas"""
        self.monitorable = enabled

    def is_monitorable(self) -> bool:
        """Check if this area can be monitored"""
        return self.monitorable

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Area2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "monitoring": self.monitoring,
            "monitorable": self.monitorable,
            "priority": self.priority,
            "gravity": self.gravity,
            "gravity_vector": self.gravity_vector.copy(),
            "linear_damp": self.linear_damp,
            "angular_damp": self.angular_damp
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Area2D":
        """Deserialize an Area2D from a dictionary."""
        area = cls(data.get("name", "Area2D"))
        cls._apply_node_properties(area, data)

        area.collision_layer = data.get("collision_layer", 1)
        area.collision_mask = data.get("collision_mask", 1)
        area.monitoring = data.get("monitoring", True)
        area.monitorable = data.get("monitorable", True)
        area.priority = data.get("priority", 0)
        area.gravity = data.get("gravity", 0.0)
        area.gravity_vector = data.get("gravity_vector", [0.0, 1.0])
        area.linear_damp = data.get("linear_damp", 0.0)
        area.angular_damp = data.get("angular_damp", 0.0)

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            area.add_child(child)
        return area
