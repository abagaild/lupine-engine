"""
Node2D implementation for Lupine Engine
Base class for all 2D nodes with transform capabilities
"""

from core.scene.node2d import Node2D as BaseNode2D
from typing import Dict, Any, List, Optional
import math


class Node2D(BaseNode2D):
    """
    Base class for 2D nodes with position, rotation, and scale.
    Provides transform hierarchy and coordinate system management.

    Features:
    - 2D transform (position, rotation, scale)
    - Global and local coordinate systems
    - Transform hierarchy with parent/child relationships
    - Z-index for depth sorting
    - Transform notifications and caching
    """
    
    def __init__(self, name: str = "Node2D"):
        super().__init__(name, "Node2D")

        # Export variables for editor
        self.export_variables.update({
            "position": {
                "type": "vector2",
                "value": [0.0, 0.0],
                "description": "Position in 2D space"
            },
            "rotation": {
                "type": "float",
                "value": 0.0,
                "min": -360.0,
                "max": 360.0,
                "step": 0.1,
                "description": "Rotation in degrees"
            },
            "scale": {
                "type": "vector2",
                "value": [1.0, 1.0],
                "min": 0.01,
                "max": 10.0,
                "step": 0.01,
                "description": "Scale factor"
            },
            "z_index": {
                "type": "int",
                "value": 0,
                "min": -1000,
                "max": 1000,
                "description": "Z-order for depth sorting"
            },
            "z_as_relative": {
                "type": "bool",
                "value": True,
                "description": "If true, z_index is relative to parent"
            }
        })
        
        # Built-in signals
        self.add_signal("transform_changed")
        self.add_signal("global_transform_changed")
    
    def _mark_transform_dirty(self):
        """Mark transform as dirty and notify children"""
        super()._mark_transform_dirty()
        self.emit_signal("transform_changed")
        
        # Mark all children as dirty too
        for child in self.children:
            if isinstance(child, Node2D):
                child._mark_transform_dirty()
    
    def set_position(self, x: float, y: float):
        """Set the position of the node"""
        old_pos = self.position.copy()
        super().set_position(x, y)
        if old_pos != self.position:
            self._mark_transform_dirty()
    
    def set_global_position(self, x: float, y: float):
        """Set the global position of the node"""
        if self.parent and isinstance(self.parent, Node2D):
            # Convert global position to local position
            parent_global_pos = self.parent.get_global_position()
            parent_global_rot = self.parent.get_global_rotation()
            parent_global_scale = self.parent.get_global_scale()
            
            # Inverse transform
            rel_x = x - parent_global_pos[0]
            rel_y = y - parent_global_pos[1]
            
            cos_rot = math.cos(-parent_global_rot)
            sin_rot = math.sin(-parent_global_rot)
            
            local_x = (rel_x * cos_rot - rel_y * sin_rot) / parent_global_scale[0]
            local_y = (rel_x * sin_rot + rel_y * cos_rot) / parent_global_scale[1]
            
            self.set_position(local_x, local_y)
        else:
            self.set_position(x, y)
    
    def set_rotation(self, rotation: float):
        """Set the rotation of the node in radians"""
        old_rot = self.rotation
        super().set_rotation(rotation)
        if old_rot != self.rotation:
            self._mark_transform_dirty()
    
    def set_rotation_degrees(self, degrees: float):
        """Set the rotation of the node in degrees"""
        self.set_rotation(math.radians(degrees))
    
    def get_rotation_degrees(self) -> float:
        """Get the rotation of the node in degrees"""
        return math.degrees(self.rotation)
    
    def set_global_rotation(self, rotation: float):
        """Set the global rotation of the node"""
        if self.parent and isinstance(self.parent, Node2D):
            parent_global_rot = self.parent.get_global_rotation()
            local_rotation = rotation - parent_global_rot
            self.set_rotation(local_rotation)
        else:
            self.set_rotation(rotation)
    
    def set_scale(self, x: float, y: float):
        """Set the scale of the node"""
        old_scale = self.scale.copy()
        super().set_scale(x, y)
        if old_scale != self.scale:
            self._mark_transform_dirty()
    
    def set_global_scale(self, x: float, y: float):
        """Set the global scale of the node"""
        if self.parent and isinstance(self.parent, Node2D):
            parent_global_scale = self.parent.get_global_scale()
            local_scale_x = x / parent_global_scale[0] if parent_global_scale[0] != 0 else 1.0
            local_scale_y = y / parent_global_scale[1] if parent_global_scale[1] != 0 else 1.0
            self.set_scale(local_scale_x, local_scale_y)
        else:
            self.set_scale(x, y)
    
    def rotate(self, angle: float):
        """Rotate the node by the given amount in radians"""
        self.set_rotation(self.rotation + angle)

    def look_at(self, target: List[float]):
        """Rotate the node to look at a specific point"""
        direction = [target[0] - self.position[0], target[1] - self.position[1]]
        angle = math.atan2(direction[1], direction[0])
        self.set_rotation(angle)
    
    def get_angle_to(self, point: List[float]) -> float:
        """Get the angle from this node to a point"""
        direction = [point[0] - self.position[0], point[1] - self.position[1]]
        return math.atan2(direction[1], direction[0])
    
    def get_distance_to(self, point: List[float]) -> float:
        """Get the distance from this node to a point"""
        dx = point[0] - self.position[0]
        dy = point[1] - self.position[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def move_toward(self, point: List[float], delta: float):
        """Move toward a point by a given distance"""
        direction = [point[0] - self.position[0], point[1] - self.position[1]]
        distance = math.sqrt(direction[0] * direction[0] + direction[1] * direction[1])
        
        if distance > 0:
            # Normalize direction
            direction[0] /= distance
            direction[1] /= distance
            
            # Move by delta amount
            move_distance = min(delta, distance)
            self.translate(direction[0] * move_distance, direction[1] * move_distance)
    
    def get_transform_matrix(self) -> List[List[float]]:
        """Get the 2D transformation matrix for this node"""
        cos_rot = math.cos(self.rotation)
        sin_rot = math.sin(self.rotation)
        
        # 2D transformation matrix
        return [
            [self.scale[0] * cos_rot, -self.scale[1] * sin_rot, self.position[0]],
            [self.scale[0] * sin_rot, self.scale[1] * cos_rot, self.position[1]],
            [0.0, 0.0, 1.0]
        ]
    
    def get_global_transform_matrix(self) -> List[List[float]]:
        """Get the global 2D transformation matrix for this node"""
        global_pos = self.get_global_position()
        global_rot = self.get_global_rotation()
        global_scale = self.get_global_scale()
        
        cos_rot = math.cos(global_rot)
        sin_rot = math.sin(global_rot)
        
        return [
            [global_scale[0] * cos_rot, -global_scale[1] * sin_rot, global_pos[0]],
            [global_scale[0] * sin_rot, global_scale[1] * cos_rot, global_pos[1]],
            [0.0, 0.0, 1.0]
        ]
    
    def transform_point(self, point: List[float]) -> List[float]:
        """Transform a point from local to global coordinates"""
        matrix = self.get_global_transform_matrix()
        x = point[0] * matrix[0][0] + point[1] * matrix[0][1] + matrix[0][2]
        y = point[0] * matrix[1][0] + point[1] * matrix[1][1] + matrix[1][2]
        return [x, y]
    
    def inverse_transform_point(self, point: List[float]) -> List[float]:
        """Transform a point from global to local coordinates"""
        global_pos = self.get_global_position()
        global_rot = self.get_global_rotation()
        global_scale = self.get_global_scale()
        
        # Translate to origin
        rel_x = point[0] - global_pos[0]
        rel_y = point[1] - global_pos[1]
        
        # Inverse rotation
        cos_rot = math.cos(-global_rot)
        sin_rot = math.sin(-global_rot)
        
        rot_x = rel_x * cos_rot - rel_y * sin_rot
        rot_y = rel_x * sin_rot + rel_y * cos_rot
        
        # Inverse scale
        local_x = rot_x / global_scale[0] if global_scale[0] != 0 else 0
        local_y = rot_y / global_scale[1] if global_scale[1] != 0 else 0
        
        return [local_x, local_y]
    
    def set_z_index(self, z_index: int):
        """Set the z-index for depth sorting"""
        self.z_index = z_index
    
    def get_z_index(self) -> int:
        """Get the z-index"""
        return self.z_index
    
    def set_z_as_relative(self, relative: bool):
        """Set whether z-index is relative to parent"""
        self.z_as_relative = relative
    
    def is_z_relative(self) -> bool:
        """Check if z-index is relative to parent"""
        return self.z_as_relative
    
    def get_relative_transform_to_node(self, node: "Node2D") -> Dict[str, Any]:
        """Get transform relative to another node"""
        if not isinstance(node, Node2D):
            return {"position": [0.0, 0.0], "rotation": 0.0, "scale": [1.0, 1.0]}
        
        # Convert our global position to the other node's local space
        our_global_pos = self.get_global_position()
        relative_pos = node.inverse_transform_point(our_global_pos)
        
        our_global_rot = self.get_global_rotation()
        other_global_rot = node.get_global_rotation()
        relative_rot = our_global_rot - other_global_rot
        
        our_global_scale = self.get_global_scale()
        other_global_scale = node.get_global_scale()
        relative_scale = [
            our_global_scale[0] / other_global_scale[0] if other_global_scale[0] != 0 else 1.0,
            our_global_scale[1] / other_global_scale[1] if other_global_scale[1] != 0 else 1.0
        ]
        
        return {
            "position": relative_pos,
            "rotation": relative_rot,
            "scale": relative_scale
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node2D":
        """Create from dictionary"""
        node = cls(data.get("name", "Node2D"))
        cls._apply_node_properties(node, data)
        
        # Apply Node2D specific properties
        node.position = data.get("position", [0.0, 0.0])
        node.rotation = data.get("rotation", 0.0)
        node.scale = data.get("scale", [1.0, 1.0])
        node.z_index = data.get("z_index", 0)
        node.z_as_relative = data.get("z_as_relative", True)
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            node.add_child(child)
        
        return node
