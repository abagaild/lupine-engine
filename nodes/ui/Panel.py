"""
Panel node implementation for Lupine Engine
Basic container control with background styling
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class Panel(Control):
    """
    Basic container control with background styling.
    
    Features:
    - Background color and texture support
    - Border styling with customizable width and color
    - Corner radius for rounded corners
    - Automatic child clipping
    - Margin and padding support
    - Shadow effects
    """
    
    def __init__(self, name: str = "Panel"):
        super().__init__(name)
        self.type = "Panel"

        # Export variables for editor
        self.export_variables.update({
            "background_color": {
                "type": "color",
                "value": [0.2, 0.2, 0.2, 0.8],
                "description": "Background color (RGBA)"
            },
            "background_texture": {
                "type": "path",
                "value": "",
                "filter": "*.png,*.jpg,*.jpeg,*.bmp,*.tga",
                "description": "Background texture file"
            },
            "texture_mode": {
                "type": "enum",
                "value": "stretch",
                "options": ["stretch", "tile", "keep", "keep_centered", "keep_aspect"],
                "description": "How the background texture is displayed"
            },
            "border_width": {
                "type": "float",
                "value": 1.0,
                "min": 0.0,
                "max": 20.0,
                "description": "Border width in pixels"
            },
            "border_color": {
                "type": "color",
                "value": [0.5, 0.5, 0.5, 1.0],
                "description": "Border color (RGBA)"
            },
            "corner_radius": {
                "type": "float",
                "value": 4.0,
                "min": 0.0,
                "max": 50.0,
                "description": "Corner radius for rounded corners"
            },
            "padding_left": {
                "type": "float",
                "value": 8.0,
                "min": 0.0,
                "description": "Left padding in pixels"
            },
            "padding_top": {
                "type": "float",
                "value": 8.0,
                "min": 0.0,
                "description": "Top padding in pixels"
            },
            "padding_right": {
                "type": "float",
                "value": 8.0,
                "min": 0.0,
                "description": "Right padding in pixels"
            },
            "padding_bottom": {
                "type": "float",
                "value": 8.0,
                "min": 0.0,
                "description": "Bottom padding in pixels"
            }
        })

        # Background properties
        self.background_color = [0.2, 0.2, 0.2, 0.8]  # Dark gray with transparency
        self.background_texture = ""
        self.texture_mode = "stretch"  # stretch, tile, keep, keep_centered, keep_aspect

        # Border properties
        self.border_width = 1.0
        self.border_color = [0.5, 0.5, 0.5, 1.0]  # Gray border
        self.corner_radius = 4.0
        
        # Layout properties
        self.margin_left = 0.0
        self.margin_top = 0.0
        self.margin_right = 0.0
        self.margin_bottom = 0.0
        self.padding_left = 8.0
        self.padding_top = 8.0
        self.padding_right = 8.0
        self.padding_bottom = 8.0
        
        # Visual effects
        self.shadow_enabled = False
        self.shadow_color = [0.0, 0.0, 0.0, 0.5]
        self.shadow_offset = [2.0, 2.0]
        self.shadow_blur = 4.0
        
        # Clipping
        self.clip_contents = True
        
        # Built-in signals
        self.add_signal("panel_resized")
    
    def _ready(self):
        """Called when panel enters the scene tree"""
        super()._ready()
        
        # Connect to resize signal to handle child layout
        self.connect("resized", self, "_on_panel_resized")
    
    def _on_panel_resized(self):
        """Handle panel resize"""
        self.emit_signal("panel_resized")
        self._update_child_layout()
    
    def _update_child_layout(self):
        """Update child positioning based on padding"""
        if not self.children:
            return
        
        # Calculate content area
        content_x = self.padding_left
        content_y = self.padding_top
        content_width = max(0, self.size[0] - self.padding_left - self.padding_right)
        content_height = max(0, self.size[1] - self.padding_top - self.padding_bottom)
        
        # For now, just ensure children are within content bounds
        # More sophisticated layout will be handled by container nodes
        for child in self.children:
            if hasattr(child, 'position') and hasattr(child, 'size'):
                # Clamp child position to content area if clipping is enabled
                if self.clip_contents:
                    child_x = max(content_x, min(child.position[0], content_x + content_width - child.size[0]))
                    child_y = max(content_y, min(child.position[1], content_y + content_height - child.size[1]))
                    child.set_position(child_x, child_y)
    
    def set_background_color(self, color: List[float]):
        """Set background color [r, g, b, a]"""
        self.background_color = color.copy() if isinstance(color, list) else list(color)
    
    def get_background_color(self) -> List[float]:
        """Get background color"""
        return self.background_color.copy()
    
    def set_border_width(self, width: float):
        """Set border width"""
        self.border_width = max(0.0, width)
    
    def get_border_width(self) -> float:
        """Get border width"""
        return self.border_width
    
    def set_border_color(self, color: List[float]):
        """Set border color [r, g, b, a]"""
        self.border_color = color.copy() if isinstance(color, list) else list(color)
    
    def get_border_color(self) -> List[float]:
        """Get border color"""
        return self.border_color.copy()
    
    def set_corner_radius(self, radius: float):
        """Set corner radius for rounded corners"""
        self.corner_radius = max(0.0, radius)
    
    def get_corner_radius(self) -> float:
        """Get corner radius"""
        return self.corner_radius
    
    def set_margin(self, left: float, top: float, right: float, bottom: float):
        """Set all margin values"""
        self.margin_left = max(0.0, left)
        self.margin_top = max(0.0, top)
        self.margin_right = max(0.0, right)
        self.margin_bottom = max(0.0, bottom)
    
    def set_padding(self, left: float, top: float, right: float, bottom: float):
        """Set all padding values"""
        self.padding_left = max(0.0, left)
        self.padding_top = max(0.0, top)
        self.padding_right = max(0.0, right)
        self.padding_bottom = max(0.0, bottom)
        self._update_child_layout()
    
    def get_content_rect(self) -> List[float]:
        """Get the content area rectangle [x, y, width, height]"""
        content_x = self.padding_left
        content_y = self.padding_top
        content_width = max(0, self.size[0] - self.padding_left - self.padding_right)
        content_height = max(0, self.size[1] - self.padding_top - self.padding_bottom)
        return [content_x, content_y, content_width, content_height]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add Panel-specific properties
        data.update({
            "background_color": self.background_color,
            "background_texture": self.background_texture,
            "texture_mode": self.texture_mode,
            "border_width": self.border_width,
            "border_color": self.border_color,
            "corner_radius": self.corner_radius,
            "margin_left": self.margin_left,
            "margin_top": self.margin_top,
            "margin_right": self.margin_right,
            "margin_bottom": self.margin_bottom,
            "padding_left": self.padding_left,
            "padding_top": self.padding_top,
            "padding_right": self.padding_right,
            "padding_bottom": self.padding_bottom,
            "shadow_enabled": self.shadow_enabled,
            "shadow_color": self.shadow_color,
            "shadow_offset": self.shadow_offset,
            "shadow_blur": self.shadow_blur,
            "clip_contents": self.clip_contents,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Panel":
        """Create from dictionary"""
        panel = cls(data.get("name", "Panel"))
        cls._apply_node_properties(panel, data)
        
        # Apply Panel properties
        panel.background_color = data.get("background_color", [0.2, 0.2, 0.2, 0.8])
        panel.background_texture = data.get("background_texture", None)
        panel.texture_mode = data.get("texture_mode", "stretch")
        panel.border_width = data.get("border_width", 1.0)
        panel.border_color = data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        panel.corner_radius = data.get("corner_radius", 4.0)
        panel.margin_left = data.get("margin_left", 0.0)
        panel.margin_top = data.get("margin_top", 0.0)
        panel.margin_right = data.get("margin_right", 0.0)
        panel.margin_bottom = data.get("margin_bottom", 0.0)
        panel.padding_left = data.get("padding_left", 8.0)
        panel.padding_top = data.get("padding_top", 8.0)
        panel.padding_right = data.get("padding_right", 8.0)
        panel.padding_bottom = data.get("padding_bottom", 8.0)
        panel.shadow_enabled = data.get("shadow_enabled", False)
        panel.shadow_color = data.get("shadow_color", [0.0, 0.0, 0.0, 0.5])
        panel.shadow_offset = data.get("shadow_offset", [2.0, 2.0])
        panel.shadow_blur = data.get("shadow_blur", 4.0)
        panel.clip_contents = data.get("clip_contents", True)
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            panel.add_child(child)
        
        return panel
    
    def __str__(self) -> str:
        """String representation of the panel"""
        return f"Panel({self.name}, rect={self.get_rect()}, bg_color={self.background_color})"
