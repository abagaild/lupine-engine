"""
Camera2D node implementation for Lupine Engine
2D camera with viewport control and following capabilities
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional
import math


class Camera2D(Node2D):
    """
    2D camera node for controlling the viewport and view.
    
    Features:
    - Viewport control and positioning
    - Camera following with smoothing
    - Zoom control
    - Camera limits and boundaries
    - Screen shake effects
    - Drag margins and dead zones
    - Current camera management
    """
    
    def __init__(self, name: str = "Camera2D"):
        super().__init__(name)
        self.type = "Camera2D"
        
        # Export variables for editor
        self.export_variables.update({
            "current": {
                "type": "bool",
                "value": False,
                "description": "Whether this camera is the current active camera"
            },
            "zoom": {
                "type": "vector2",
                "value": [1.0, 1.0],
                "min": 0.001,
                "description": "Camera zoom level"
            },
            "enabled": {
                "type": "bool",
                "value": True,
                "description": "Whether the camera is enabled"
            },
            "smoothing_enabled": {
                "type": "bool",
                "value": False,
                "description": "Enable camera smoothing"
            },
            "smoothing_speed": {
                "type": "float",
                "value": 5.0,
                "min": 0.1,
                "max": 50.0,
                "description": "Camera smoothing speed"
            },
            "rotating": {
                "type": "bool",
                "value": False,
                "description": "Whether camera rotates with the node"
            },
            "limit_left": {
                "type": "int",
                "value": -10000000,
                "description": "Left camera limit"
            },
            "limit_top": {
                "type": "int",
                "value": -10000000,
                "description": "Top camera limit"
            },
            "limit_right": {
                "type": "int",
                "value": 10000000,
                "description": "Right camera limit"
            },
            "limit_bottom": {
                "type": "int",
                "value": 10000000,
                "description": "Bottom camera limit"
            },
            "follow_target": {
                "type": "nodepath",
                "value": "",
                "description": "Node to follow automatically"
            }
        })
        
        # Camera properties
        self.current: bool = False
        self.zoom: List[float] = [1.0, 1.0]
        self.enabled: bool = True
        self.smoothing_enabled: bool = False
        self.smoothing_speed: float = 5.0
        self.rotating: bool = False
        
        # Camera limits
        self.limit_left: int = -10000000
        self.limit_top: int = -10000000
        self.limit_right: int = 10000000
        self.limit_bottom: int = 10000000
        self.limit_smoothed: bool = False
        
        # Drag margins (for following)
        self.drag_margin_left: float = 0.2
        self.drag_margin_top: float = 0.2
        self.drag_margin_right: float = 0.2
        self.drag_margin_bottom: float = 0.2
        
        # Following
        self._follow_target: Optional[Node2D] = None
        self._target_position: List[float] = [0.0, 0.0]
        
        # Screen shake
        self._shake_intensity: float = 0.0
        self._shake_duration: float = 0.0
        self._shake_timer: float = 0.0
        self._shake_offset: List[float] = [0.0, 0.0]
        
        # Viewport size (set by renderer)
        self._viewport_size: List[int] = [1024, 768]
        
        # Built-in signals
        self.add_signal("camera_entered")
        self.add_signal("camera_exited")
        
        # Global camera registry
        if not hasattr(Camera2D, '_cameras'):
            Camera2D._cameras = []
        Camera2D._cameras.append(self)
    
    def _ready(self):
        """Called when camera enters the scene tree"""
        super()._ready()
        
        if self.current:
            self.make_current()
    
    def _process(self, delta: float):
        """Process camera updates"""
        super()._process(delta)
        
        if not self.enabled:
            return
        
        # Update screen shake
        if self._shake_timer > 0:
            self._update_screen_shake(delta)
        
        # Update following
        if self._follow_target and self.smoothing_enabled:
            self._update_smooth_following(delta)
    
    def make_current(self):
        """Make this camera the current active camera"""
        # Disable all other cameras
        for camera in Camera2D._cameras:
            if camera != self:
                camera.current = False
        
        self.current = True
        self.emit_signal("camera_entered")
    
    def clear_current(self):
        """Clear this camera as current"""
        if self.current:
            self.current = False
            self.emit_signal("camera_exited")
    
    def is_current(self) -> bool:
        """Check if this camera is current"""
        return self.current
    
    def set_zoom(self, x: float, y: float):
        """Set the camera zoom"""
        self.zoom = [max(0.001, x), max(0.001, y)]
    
    def get_zoom(self) -> List[float]:
        """Get the camera zoom"""
        return self.zoom.copy()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the camera"""
        self.enabled = enabled
    
    def is_enabled(self) -> bool:
        """Check if the camera is enabled"""
        return self.enabled
    
    def set_smoothing_enabled(self, enabled: bool):
        """Enable or disable camera smoothing"""
        self.smoothing_enabled = enabled
    
    def is_smoothing_enabled(self) -> bool:
        """Check if smoothing is enabled"""
        return self.smoothing_enabled
    
    def set_smoothing_speed(self, speed: float):
        """Set the smoothing speed"""
        self.smoothing_speed = max(0.1, speed)
    
    def get_smoothing_speed(self) -> float:
        """Get the smoothing speed"""
        return self.smoothing_speed
    
    def set_rotating(self, rotating: bool):
        """Set whether camera rotates with the node"""
        self.rotating = rotating
    
    def is_rotating(self) -> bool:
        """Check if camera rotates"""
        return self.rotating
    
    def set_limit(self, margin: str, value: int):
        """Set a camera limit"""
        if margin == "left":
            self.limit_left = value
        elif margin == "top":
            self.limit_top = value
        elif margin == "right":
            self.limit_right = value
        elif margin == "bottom":
            self.limit_bottom = value
    
    def get_limit(self, margin: str) -> int:
        """Get a camera limit"""
        if margin == "left":
            return self.limit_left
        elif margin == "top":
            return self.limit_top
        elif margin == "right":
            return self.limit_right
        elif margin == "bottom":
            return self.limit_bottom
        return 0
    
    def set_drag_margin(self, margin: str, value: float):
        """Set a drag margin"""
        value = max(0.0, min(1.0, value))
        if margin == "left":
            self.drag_margin_left = value
        elif margin == "top":
            self.drag_margin_top = value
        elif margin == "right":
            self.drag_margin_right = value
        elif margin == "bottom":
            self.drag_margin_bottom = value
    
    def get_drag_margin(self, margin: str) -> float:
        """Get a drag margin"""
        if margin == "left":
            return self.drag_margin_left
        elif margin == "top":
            return self.drag_margin_top
        elif margin == "right":
            return self.drag_margin_right
        elif margin == "bottom":
            return self.drag_margin_bottom
        return 0.0
    
    def follow_target(self, target: Optional[Node2D]):
        """Set a target to follow"""
        self._follow_target = target
        if target:
            self._target_position = target.get_global_position()
    
    def get_follow_target(self) -> Optional[Node2D]:
        """Get the current follow target"""
        return self._follow_target
    
    def _update_smooth_following(self, delta: float):
        """Update smooth camera following"""
        if not self._follow_target:
            return
        
        target_pos = self._follow_target.get_global_position()
        current_pos = self.get_global_position()
        
        # Calculate desired position
        desired_pos = target_pos.copy()
        
        # Apply smoothing
        lerp_factor = min(1.0, self.smoothing_speed * delta)
        new_pos = [
            current_pos[0] + (desired_pos[0] - current_pos[0]) * lerp_factor,
            current_pos[1] + (desired_pos[1] - current_pos[1]) * lerp_factor
        ]
        
        # Apply limits
        new_pos = self._apply_limits(new_pos)
        
        # Set position
        self.set_global_position(new_pos[0], new_pos[1])
    
    def _apply_limits(self, position: List[float]) -> List[float]:
        """Apply camera limits to a position"""
        # Calculate half viewport size in world coordinates
        half_width = (self._viewport_size[0] / 2) / self.zoom[0]
        half_height = (self._viewport_size[1] / 2) / self.zoom[1]
        
        # Apply limits
        x = max(self.limit_left + half_width, min(position[0], self.limit_right - half_width))
        y = max(self.limit_top + half_height, min(position[1], self.limit_bottom - half_height))
        
        return [x, y]
    
    def start_screen_shake(self, intensity: float, duration: float):
        """Start screen shake effect"""
        self._shake_intensity = intensity
        self._shake_duration = duration
        self._shake_timer = duration
    
    def stop_screen_shake(self):
        """Stop screen shake effect"""
        self._shake_timer = 0.0
        self._shake_offset = [0.0, 0.0]
    
    def _update_screen_shake(self, delta: float):
        """Update screen shake effect"""
        self._shake_timer -= delta
        
        if self._shake_timer <= 0:
            self._shake_offset = [0.0, 0.0]
            return
        
        # Calculate shake intensity based on remaining time
        intensity = self._shake_intensity * (self._shake_timer / self._shake_duration)
        
        # Generate random offset
        import random
        self._shake_offset = [
            (random.random() - 0.5) * 2 * intensity,
            (random.random() - 0.5) * 2 * intensity
        ]
    
    def get_camera_position(self) -> List[float]:
        """Get the effective camera position including shake"""
        pos = self.get_global_position()
        return [
            pos[0] + self._shake_offset[0],
            pos[1] + self._shake_offset[1]
        ]
    
    def get_camera_transform(self) -> Dict[str, Any]:
        """Get the camera transform for rendering"""
        pos = self.get_camera_position()
        
        return {
            "position": pos,
            "rotation": self.get_global_rotation() if self.rotating else 0.0,
            "zoom": self.zoom.copy(),
            "viewport_size": self._viewport_size.copy()
        }
    
    def screen_to_world(self, screen_pos: List[float]) -> List[float]:
        """Convert screen coordinates to world coordinates"""
        camera_pos = self.get_camera_position()
        
        # Center screen coordinates
        centered_x = screen_pos[0] - self._viewport_size[0] / 2
        centered_y = screen_pos[1] - self._viewport_size[1] / 2
        
        # Apply zoom
        world_x = centered_x / self.zoom[0] + camera_pos[0]
        world_y = centered_y / self.zoom[1] + camera_pos[1]
        
        return [world_x, world_y]
    
    def world_to_screen(self, world_pos: List[float]) -> List[float]:
        """Convert world coordinates to screen coordinates"""
        camera_pos = self.get_camera_position()
        
        # Relative to camera
        rel_x = (world_pos[0] - camera_pos[0]) * self.zoom[0]
        rel_y = (world_pos[1] - camera_pos[1]) * self.zoom[1]
        
        # Convert to screen coordinates
        screen_x = rel_x + self._viewport_size[0] / 2
        screen_y = rel_y + self._viewport_size[1] / 2
        
        return [screen_x, screen_y]
    
    def set_viewport_size(self, width: int, height: int):
        """Set the viewport size (called by renderer)"""
        self._viewport_size = [width, height]
    
    def get_viewport_size(self) -> List[int]:
        """Get the viewport size"""
        return self._viewport_size.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "current": self.current,
            "zoom": self.zoom.copy(),
            "enabled": self.enabled,
            "smoothing_enabled": self.smoothing_enabled,
            "smoothing_speed": self.smoothing_speed,
            "rotating": self.rotating,
            "limit_left": self.limit_left,
            "limit_top": self.limit_top,
            "limit_right": self.limit_right,
            "limit_bottom": self.limit_bottom,
            "drag_margin_left": self.drag_margin_left,
            "drag_margin_top": self.drag_margin_top,
            "drag_margin_right": self.drag_margin_right,
            "drag_margin_bottom": self.drag_margin_bottom
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Camera2D":
        """Create from dictionary"""
        camera = cls(data.get("name", "Camera2D"))
        cls._apply_node_properties(camera, data)
        
        # Apply Node2D properties
        camera.position = data.get("position", [0.0, 0.0])
        camera.rotation = data.get("rotation", 0.0)
        camera.scale = data.get("scale", [1.0, 1.0])
        camera.z_index = data.get("z_index", 0)
        camera.z_as_relative = data.get("z_as_relative", True)
        
        # Apply Camera2D properties
        camera.current = data.get("current", False)
        camera.zoom = data.get("zoom", [1.0, 1.0])
        camera.enabled = data.get("enabled", True)
        camera.smoothing_enabled = data.get("smoothing_enabled", False)
        camera.smoothing_speed = data.get("smoothing_speed", 5.0)
        camera.rotating = data.get("rotating", False)
        camera.limit_left = data.get("limit_left", -10000000)
        camera.limit_top = data.get("limit_top", -10000000)
        camera.limit_right = data.get("limit_right", 10000000)
        camera.limit_bottom = data.get("limit_bottom", 10000000)
        camera.drag_margin_left = data.get("drag_margin_left", 0.2)
        camera.drag_margin_top = data.get("drag_margin_top", 0.2)
        camera.drag_margin_right = data.get("drag_margin_right", 0.2)
        camera.drag_margin_bottom = data.get("drag_margin_bottom", 0.2)
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            camera.add_child(child)
        
        return camera
