"""
Node2D - Base class for 2D nodes with transform
"""

from typing import Dict, Any, List, Optional, Tuple
from .base_node import Node


class Node2D(Node):
    """Base class for 2D nodes with position, rotation, and scale"""
    
    def __init__(self, name: str = "Node2D", node_type: str = "Node2D"):
        super().__init__(name, node_type)
        
        # Transform properties
        self.position: List[float] = [0.0, 0.0]
        self.rotation: float = 0.0
        self.scale: List[float] = [1.0, 1.0]
        self.z_index: int = 0
        self.z_as_relative: bool = True
        
        # Global transform cache
        self._global_position: Optional[List[float]] = None
        self._global_rotation: Optional[float] = None
        self._global_scale: Optional[List[float]] = None
        self._transform_dirty: bool = True
    
    def set_position(self, x: float, y: float):
        """Set the position of the node"""
        self.position = [x, y]
        self._mark_transform_dirty()
    
    def get_position(self) -> List[float]:
        """Get the position of the node"""
        return self.position.copy()
    
    def set_rotation(self, rotation: float):
        """Set the rotation of the node in radians"""
        self.rotation = rotation
        self._mark_transform_dirty()
    
    def get_rotation(self) -> float:
        """Get the rotation of the node in radians"""
        return self.rotation
    
    def set_scale(self, x: float, y: float):
        """Set the scale of the node"""
        self.scale = [x, y]
        self._mark_transform_dirty()
    
    def get_scale(self) -> List[float]:
        """Get the scale of the node"""
        return self.scale.copy()
    
    def translate(self, x: float, y: float):
        """Translate the node by the given offset"""
        self.position[0] += x
        self.position[1] += y
        self._mark_transform_dirty()
    
    def rotate(self, angle: float):
        """Rotate the node by the given angle in radians"""
        self.rotation += angle
        self._mark_transform_dirty()
    
    def look_at(self, target: List[float]):
        """Make the node look at the target position"""
        import math
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        self.rotation = math.atan2(dy, dx)
        self._mark_transform_dirty()
    
    def get_global_position(self) -> List[float]:
        """Get the global position of the node"""
        if self._transform_dirty or self._global_position is None:
            self._update_global_transform()
        return self._global_position.copy()
    
    def get_global_rotation(self) -> float:
        """Get the global rotation of the node"""
        if self._transform_dirty or self._global_rotation is None:
            self._update_global_transform()
        return self._global_rotation
    
    def get_global_scale(self) -> List[float]:
        """Get the global scale of the node"""
        if self._transform_dirty or self._global_scale is None:
            self._update_global_transform()
        return self._global_scale.copy()
    
    def _mark_transform_dirty(self):
        """Mark transform as dirty and propagate to children"""
        self._transform_dirty = True
        for child in self.children:
            if isinstance(child, Node2D):
                child._mark_transform_dirty()
    
    def _update_global_transform(self):
        """Update global transform from parent chain"""
        if self.parent and isinstance(self.parent, Node2D):
            parent_pos = self.parent.get_global_position()
            parent_rot = self.parent.get_global_rotation()
            parent_scale = self.parent.get_global_scale()
            
            # Apply parent transform
            import math
            cos_rot = math.cos(parent_rot)
            sin_rot = math.sin(parent_rot)
            
            # Transform position
            local_x = self.position[0] * parent_scale[0]
            local_y = self.position[1] * parent_scale[1]
            
            self._global_position = [
                parent_pos[0] + (local_x * cos_rot - local_y * sin_rot),
                parent_pos[1] + (local_x * sin_rot + local_y * cos_rot)
            ]
            
            # Transform rotation and scale
            self._global_rotation = parent_rot + self.rotation
            self._global_scale = [
                parent_scale[0] * self.scale[0],
                parent_scale[1] * self.scale[1]
            ]
        else:
            # No parent, use local transform
            self._global_position = self.position.copy()
            self._global_rotation = self.rotation
            self._global_scale = self.scale.copy()
        
        self._transform_dirty = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()

        # Only include Node2D properties if they exist (some subclasses might not have them)
        node2d_data = {}
        if hasattr(self, 'position'):
            node2d_data["position"] = self.position.copy() if hasattr(self.position, 'copy') else list(self.position)
        if hasattr(self, 'rotation'):
            node2d_data["rotation"] = self.rotation
        if hasattr(self, 'scale'):
            node2d_data["scale"] = self.scale.copy() if hasattr(self.scale, 'copy') else list(self.scale)
        if hasattr(self, 'z_index'):
            node2d_data["z_index"] = self.z_index
        if hasattr(self, 'z_as_relative'):
            node2d_data["z_as_relative"] = self.z_as_relative

        data.update(node2d_data)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node2D":
        """Create from dictionary"""
        node = cls(data.get("name", "Node2D"), data.get("type", "Node2D"))
        cls._apply_node_properties(node, data)
        
        # Apply Node2D specific properties
        node.position = data.get("position", [0.0, 0.0])
        node.rotation = data.get("rotation", 0.0)
        node.scale = data.get("scale", [1.0, 1.0])
        node.z_index = data.get("z_index", 0)
        node.z_as_relative = data.get("z_as_relative", True)
        
        # Create children using proper node loading
        for child_data in data.get("children", []):
            try:
                # Try to use the scene manager's node creation method
                from .scene_manager import Scene
                child = Scene._create_node_from_dict(child_data)
                node.add_child(child)
            except ImportError:
                # Fallback to base Node
                child = Node.from_dict(child_data)
                node.add_child(child)
        
        return node
