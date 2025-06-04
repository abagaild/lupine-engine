"""
ColorRect node implementation for Lupine Engine
Simple colored rectangle control for UI backgrounds and dividers
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class ColorRect(Control):
    """
    Simple colored rectangle control for UI backgrounds and dividers.
    
    Features:
    - Solid color fill
    - Gradient support (linear and radial)
    - Border styling
    - Corner radius for rounded rectangles
    - Transparency support
    - Animation-friendly color properties
    """
    
    def __init__(self, name: str = "ColorRect"):
        super().__init__(name)
        self.type = "ColorRect"
        
        # Color properties
        self.color = [1.0, 1.0, 1.0, 1.0]  # White by default
        
        # Gradient properties
        self.gradient_enabled = False
        self.gradient_type = "linear"  # linear, radial
        self.gradient_start_color = [1.0, 1.0, 1.0, 1.0]
        self.gradient_end_color = [0.0, 0.0, 0.0, 1.0]
        self.gradient_angle = 0.0  # For linear gradients (degrees)
        self.gradient_center = [0.5, 0.5]  # For radial gradients (normalized)
        self.gradient_radius = 0.5  # For radial gradients (normalized)
        
        # Border properties
        self.border_enabled = False
        self.border_width = 1.0
        self.border_color = [0.0, 0.0, 0.0, 1.0]  # Black border
        
        # Corner properties
        self.corner_radius = 0.0
        self.corner_detail = 8  # Number of segments for rounded corners
        
        # Animation properties
        self.color_transition_duration = 0.0  # 0 = instant
        self._target_color = None
        self._color_transition_time = 0.0
        
        # Built-in signals
        self.add_signal("color_changed")
    
    def _process(self, delta: float):
        """Process color transitions"""
        super()._process(delta)
        
        if self._target_color and self.color_transition_duration > 0:
            self._color_transition_time += delta
            progress = min(1.0, self._color_transition_time / self.color_transition_duration)
            
            # Interpolate color
            for i in range(4):  # RGBA
                self.color[i] = self.color[i] + (self._target_color[i] - self.color[i]) * progress
            
            if progress >= 1.0:
                self.color = self._target_color.copy()
                self._target_color = None
                self._color_transition_time = 0.0
                self.emit_signal("color_changed", self.color)
    
    def set_color(self, color: List[float], animate: bool = False):
        """Set the color [r, g, b, a]"""
        if animate and self.color_transition_duration > 0:
            self._target_color = color.copy() if isinstance(color, list) else list(color)
            self._color_transition_time = 0.0
        else:
            old_color = self.color.copy()
            self.color = color.copy() if isinstance(color, list) else list(color)
            if old_color != self.color:
                self.emit_signal("color_changed", self.color)
    
    def get_color(self) -> List[float]:
        """Get the current color"""
        return self.color.copy()
    
    def set_gradient(self, enabled: bool, gradient_type: str = "linear", 
                    start_color: List[float] = None, end_color: List[float] = None):
        """Configure gradient settings"""
        self.gradient_enabled = enabled
        self.gradient_type = gradient_type
        
        if start_color:
            self.gradient_start_color = start_color.copy() if isinstance(start_color, list) else list(start_color)
        if end_color:
            self.gradient_end_color = end_color.copy() if isinstance(end_color, list) else list(end_color)
    
    def set_gradient_angle(self, angle: float):
        """Set gradient angle in degrees (for linear gradients)"""
        self.gradient_angle = angle % 360.0
    
    def set_gradient_center(self, center: List[float]):
        """Set gradient center [x, y] normalized (for radial gradients)"""
        self.gradient_center = [max(0.0, min(1.0, center[0])), max(0.0, min(1.0, center[1]))]
    
    def set_gradient_radius(self, radius: float):
        """Set gradient radius normalized (for radial gradients)"""
        self.gradient_radius = max(0.0, min(1.0, radius))
    
    def set_border(self, enabled: bool, width: float = 1.0, color: List[float] = None):
        """Configure border settings"""
        self.border_enabled = enabled
        self.border_width = max(0.0, width)
        
        if color:
            self.border_color = color.copy() if isinstance(color, list) else list(color)
    
    def set_corner_radius(self, radius: float, detail: int = 8):
        """Set corner radius and detail level"""
        self.corner_radius = max(0.0, radius)
        self.corner_detail = max(3, detail)
    
    def set_color_transition_duration(self, duration: float):
        """Set color transition duration for animations"""
        self.color_transition_duration = max(0.0, duration)
    
    def get_effective_color(self) -> List[float]:
        """Get the effective color (considering modulation)"""
        if hasattr(self, 'modulate'):
            # Apply modulation to color
            modulated = []
            for i in range(4):
                modulated.append(self.color[i] * self.modulate[i])
            return modulated
        return self.color.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add ColorRect-specific properties
        data.update({
            "color": self.color,
            "gradient_enabled": self.gradient_enabled,
            "gradient_type": self.gradient_type,
            "gradient_start_color": self.gradient_start_color,
            "gradient_end_color": self.gradient_end_color,
            "gradient_angle": self.gradient_angle,
            "gradient_center": self.gradient_center,
            "gradient_radius": self.gradient_radius,
            "border_enabled": self.border_enabled,
            "border_width": self.border_width,
            "border_color": self.border_color,
            "corner_radius": self.corner_radius,
            "corner_detail": self.corner_detail,
            "color_transition_duration": self.color_transition_duration,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorRect":
        """Create from dictionary"""
        color_rect = cls(data.get("name", "ColorRect"))
        cls._apply_node_properties(color_rect, data)
        
        # Apply ColorRect properties
        color_rect.color = data.get("color", [1.0, 1.0, 1.0, 1.0])
        color_rect.gradient_enabled = data.get("gradient_enabled", False)
        color_rect.gradient_type = data.get("gradient_type", "linear")
        color_rect.gradient_start_color = data.get("gradient_start_color", [1.0, 1.0, 1.0, 1.0])
        color_rect.gradient_end_color = data.get("gradient_end_color", [0.0, 0.0, 0.0, 1.0])
        color_rect.gradient_angle = data.get("gradient_angle", 0.0)
        color_rect.gradient_center = data.get("gradient_center", [0.5, 0.5])
        color_rect.gradient_radius = data.get("gradient_radius", 0.5)
        color_rect.border_enabled = data.get("border_enabled", False)
        color_rect.border_width = data.get("border_width", 1.0)
        color_rect.border_color = data.get("border_color", [0.0, 0.0, 0.0, 1.0])
        color_rect.corner_radius = data.get("corner_radius", 0.0)
        color_rect.corner_detail = data.get("corner_detail", 8)
        color_rect.color_transition_duration = data.get("color_transition_duration", 0.0)
        
        # Initialize transition state
        color_rect._target_color = None
        color_rect._color_transition_time = 0.0
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            color_rect.add_child(child)
        
        return color_rect
    
    def __str__(self) -> str:
        """String representation of the color rect"""
        return f"ColorRect({self.name}, rect={self.get_rect()}, color={self.color})"
