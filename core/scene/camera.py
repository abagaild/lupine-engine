"""
Camera2D - 2D camera node for viewport control
"""

from typing import Dict, Any, List, Optional
from .node2d import Node2D


class Camera2D(Node2D):
    """2D camera node for controlling the viewport"""
    
    def __init__(self, name: str = "Camera2D", node_type: str = "Camera2D"):
        super().__init__(name, node_type)
        
        # Camera properties
        self.current: bool = False
        self.enabled: bool = True
        self.zoom: List[float] = [1.0, 1.0]
        self.offset: List[float] = [0.0, 0.0]
        
        # Following properties
        self.follow_target: Optional[str] = None  # Node path to follow
        self.follow_smoothing: bool = False
        self.follow_speed: float = 5.0
        
        # Limits
        self.limit_left: Optional[float] = None
        self.limit_top: Optional[float] = None
        self.limit_right: Optional[float] = None
        self.limit_bottom: Optional[float] = None
        self.limit_smoothed: bool = False
        
        # Drag margins (for following)
        self.drag_margin_left: float = 0.2
        self.drag_margin_top: float = 0.2
        self.drag_margin_right: float = 0.2
        self.drag_margin_bottom: float = 0.2
        
        # Smoothing
        self.smoothing_enabled: bool = False
        self.smoothing_speed: float = 5.0
        
        # Shake effect
        self.shake_intensity: float = 0.0
        self.shake_duration: float = 0.0
        self.shake_timer: float = 0.0
        
        # Internal state
        self._target_position: List[float] = [0.0, 0.0]
        self._shake_offset: List[float] = [0.0, 0.0]
    
    def make_current(self):
        """Make this camera the current active camera"""
        self.current = True
        # TODO: Notify camera manager to set this as active
    
    def is_current(self) -> bool:
        """Check if this camera is the current active camera"""
        return self.current
    
    def set_zoom(self, x: float, y: float):
        """Set the camera zoom"""
        self.zoom = [max(0.01, x), max(0.01, y)]  # Prevent zero/negative zoom
    
    def get_zoom(self) -> List[float]:
        """Get the camera zoom"""
        return self.zoom.copy()
    
    def set_offset(self, x: float, y: float):
        """Set the camera offset"""
        self.offset = [x, y]
    
    def get_offset(self) -> List[float]:
        """Get the camera offset"""
        return self.offset.copy()
    
    def set_follow_target(self, target_path: str):
        """Set the node to follow"""
        self.follow_target = target_path
    
    def clear_follow_target(self):
        """Clear the follow target"""
        self.follow_target = None
    
    def set_limits(self, left: float, top: float, right: float, bottom: float):
        """Set camera movement limits"""
        self.limit_left = left
        self.limit_top = top
        self.limit_right = right
        self.limit_bottom = bottom
    
    def clear_limits(self):
        """Clear camera movement limits"""
        self.limit_left = None
        self.limit_top = None
        self.limit_right = None
        self.limit_bottom = None
    
    def start_shake(self, intensity: float, duration: float):
        """Start camera shake effect"""
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_timer = duration
    
    def stop_shake(self):
        """Stop camera shake effect"""
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_timer = 0.0
        self._shake_offset = [0.0, 0.0]
    
    def update_shake(self, delta: float):
        """Update shake effect"""
        if self.shake_timer > 0:
            self.shake_timer -= delta
            if self.shake_timer <= 0:
                self.stop_shake()
            else:
                # Generate random shake offset
                import random
                intensity = self.shake_intensity * (self.shake_timer / self.shake_duration)
                self._shake_offset = [
                    random.uniform(-intensity, intensity),
                    random.uniform(-intensity, intensity)
                ]
    
    def get_camera_position(self) -> List[float]:
        """Get the final camera position including shake"""
        pos = self.get_global_position()
        return [
            pos[0] + self.offset[0] + self._shake_offset[0],
            pos[1] + self.offset[1] + self._shake_offset[1]
        ]
    
    def get_viewport_rect(self, viewport_size: List[float]) -> List[float]:
        """Get the viewport rectangle in world coordinates"""
        cam_pos = self.get_camera_position()
        width = viewport_size[0] / self.zoom[0]
        height = viewport_size[1] / self.zoom[1]
        
        return [
            cam_pos[0] - width / 2,
            cam_pos[1] - height / 2,
            width,
            height
        ]
    
    def world_to_screen(self, world_pos: List[float], viewport_size: List[float]) -> List[float]:
        """Convert world coordinates to screen coordinates"""
        cam_pos = self.get_camera_position()
        
        # Relative to camera
        rel_x = (world_pos[0] - cam_pos[0]) * self.zoom[0]
        rel_y = (world_pos[1] - cam_pos[1]) * self.zoom[1]
        
        # Screen coordinates (center of viewport is 0,0)
        screen_x = rel_x + viewport_size[0] / 2
        screen_y = rel_y + viewport_size[1] / 2
        
        return [screen_x, screen_y]
    
    def screen_to_world(self, screen_pos: List[float], viewport_size: List[float]) -> List[float]:
        """Convert screen coordinates to world coordinates"""
        cam_pos = self.get_camera_position()
        
        # Relative to viewport center
        rel_x = screen_pos[0] - viewport_size[0] / 2
        rel_y = screen_pos[1] - viewport_size[1] / 2
        
        # World coordinates
        world_x = cam_pos[0] + rel_x / self.zoom[0]
        world_y = cam_pos[1] + rel_y / self.zoom[1]
        
        return [world_x, world_y]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "current": self.current,
            "enabled": self.enabled,
            "zoom": self.zoom.copy(),
            "offset": self.offset.copy(),
            "follow_target": self.follow_target,
            "follow_smoothing": self.follow_smoothing,
            "follow_speed": self.follow_speed,
            "limit_left": self.limit_left,
            "limit_top": self.limit_top,
            "limit_right": self.limit_right,
            "limit_bottom": self.limit_bottom,
            "limit_smoothed": self.limit_smoothed,
            "drag_margin_left": self.drag_margin_left,
            "drag_margin_top": self.drag_margin_top,
            "drag_margin_right": self.drag_margin_right,
            "drag_margin_bottom": self.drag_margin_bottom,
            "smoothing_enabled": self.smoothing_enabled,
            "smoothing_speed": self.smoothing_speed
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Camera2D":
        """Create from dictionary"""
        node = cls(data.get("name", "Camera2D"), data.get("type", "Camera2D"))
        cls._apply_node_properties(node, data)
        
        # Apply Node2D properties
        node.position = data.get("position", [0.0, 0.0])
        node.rotation = data.get("rotation", 0.0)
        node.scale = data.get("scale", [1.0, 1.0])
        node.z_index = data.get("z_index", 0)
        node.z_as_relative = data.get("z_as_relative", True)
        
        # Apply Camera2D specific properties
        node.current = data.get("current", False)
        node.enabled = data.get("enabled", True)
        node.zoom = data.get("zoom", [1.0, 1.0])
        node.offset = data.get("offset", [0.0, 0.0])
        node.follow_target = data.get("follow_target")
        node.follow_smoothing = data.get("follow_smoothing", False)
        node.follow_speed = data.get("follow_speed", 5.0)
        node.limit_left = data.get("limit_left")
        node.limit_top = data.get("limit_top")
        node.limit_right = data.get("limit_right")
        node.limit_bottom = data.get("limit_bottom")
        node.limit_smoothed = data.get("limit_smoothed", False)
        node.drag_margin_left = data.get("drag_margin_left", 0.2)
        node.drag_margin_top = data.get("drag_margin_top", 0.2)
        node.drag_margin_right = data.get("drag_margin_right", 0.2)
        node.drag_margin_bottom = data.get("drag_margin_bottom", 0.2)
        node.smoothing_enabled = data.get("smoothing_enabled", False)
        node.smoothing_speed = data.get("smoothing_speed", 5.0)
        
        # Create children
        for child_data in data.get("children", []):
            from .base_node import Node
            child = Node.from_dict(child_data)
            node.add_child(child)
        
        return node
