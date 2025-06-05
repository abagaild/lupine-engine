"""
TextureRect node implementation for Lupine Engine
Textured rectangle control with various scaling and display modes
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class TextureRect(Control):
    """
    Textured rectangle control with various scaling and display modes.
    
    Features:
    - Texture loading and display
    - Multiple stretch modes (stretch, tile, keep, keep_centered, keep_aspect, keep_aspect_centered)
    - Texture filtering options
    - UV coordinate manipulation
    - Texture modulation (color tinting)
    - Flip and rotation support
    - Texture region selection
    """
    
    def __init__(self, name: str = "TextureRect"):
        super().__init__(name)
        self.type = "TextureRect"

        # Export variables for editor
        self.export_variables.update({
            "texture": {
                "type": "path",
                "value": "",
                "filter": "*.png,*.jpg,*.jpeg,*.bmp,*.tga",
                "description": "Texture file to display"
            },
            "stretch_mode": {
                "type": "enum",
                "value": "stretch",
                "options": ["stretch", "tile", "keep", "keep_centered", "keep_aspect", "keep_aspect_centered"],
                "description": "How the texture is stretched to fit the control"
            },
            "expand": {
                "type": "bool",
                "value": False,
                "description": "Whether to expand beyond the control's size"
            },
            "filter": {
                "type": "bool",
                "value": True,
                "description": "Enable linear texture filtering"
            },
            "flip_h": {
                "type": "bool",
                "value": False,
                "description": "Flip texture horizontally"
            },
            "flip_v": {
                "type": "bool",
                "value": False,
                "description": "Flip texture vertically"
            },
            "modulate_color": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Color modulation (tint)"
            }
        })

        # Texture properties
        self.texture_path = ""
        self.texture = ""  # Export variable for texture path
        
        # Display properties
        self.stretch_mode = "stretch"  # stretch, tile, keep, keep_centered, keep_aspect, keep_aspect_centered
        self.expand = False  # Whether to expand beyond the control's size
        
        # Texture filtering
        self.filter = True  # Linear filtering vs nearest neighbor
        
        # UV manipulation
        self.uv_offset = [0.0, 0.0]  # UV offset for scrolling effects
        self.uv_scale = [1.0, 1.0]   # UV scale for tiling
        
        # Transformation
        self.flip_h = False  # Horizontal flip
        self.flip_v = False  # Vertical flip
        self.rotation = 0.0  # Rotation in degrees
        
        # Texture region (for sprite sheets)
        self.use_region = False
        self.region_rect = [0.0, 0.0, 1.0, 1.0]  # Normalized coordinates [x, y, width, height]
        
        # Color modulation
        self.modulate_color = [1.0, 1.0, 1.0, 1.0]  # RGBA multiplier
        
        # Animation properties
        self.uv_animation_speed = [0.0, 0.0]  # UV scrolling speed
        
        # Built-in signals
        self.add_signal("texture_changed")

    def _on_export_variable_changed(self, var_name: str, value):
        """Handle export variable changes"""
        super()._on_export_variable_changed(var_name, value)

        # Sync texture export variable with internal texture_path
        if var_name == "texture":
            self.texture_path = value
            self.texture = value  # Keep export variable in sync
            self.emit_signal("texture_changed", value)
    
    def _process(self, delta: float):
        """Process UV animations"""
        super()._process(delta)
        
        # Handle UV scrolling animation
        if self.uv_animation_speed[0] != 0.0 or self.uv_animation_speed[1] != 0.0:
            self.uv_offset[0] += self.uv_animation_speed[0] * delta
            self.uv_offset[1] += self.uv_animation_speed[1] * delta
            
            # Wrap UV coordinates to prevent overflow
            self.uv_offset[0] = self.uv_offset[0] % 1.0
            self.uv_offset[1] = self.uv_offset[1] % 1.0
    
    def set_texture(self, texture_path: str):
        """Set the texture from a file path"""
        old_path = self.texture_path
        self.texture_path = texture_path
        
        # The actual texture loading will be handled by the rendering system
        # This just stores the path for serialization and reference
        
        if old_path != texture_path:
            self.emit_signal("texture_changed", texture_path)
    
    def get_texture_path(self) -> Optional[str]:
        """Get the texture file path"""
        return self.texture_path
    
    def set_stretch_mode(self, mode: str):
        """Set the stretch mode"""
        valid_modes = ["stretch", "tile", "keep", "keep_centered", "keep_aspect", "keep_aspect_centered"]
        if mode in valid_modes:
            self.stretch_mode = mode
        else:
            print(f"Warning: Invalid stretch mode '{mode}'. Valid modes: {valid_modes}")
    
    def get_stretch_mode(self) -> str:
        """Get the stretch mode"""
        return self.stretch_mode
    
    def set_expand(self, expand: bool):
        """Set whether to expand beyond control size"""
        self.expand = expand
    
    def set_filter(self, filter_enabled: bool):
        """Set texture filtering"""
        self.filter = filter_enabled
    
    def set_uv_offset(self, offset: List[float]):
        """Set UV offset for scrolling effects"""
        self.uv_offset = offset.copy() if isinstance(offset, list) else list(offset)
    
    def get_uv_offset(self) -> List[float]:
        """Get UV offset"""
        return self.uv_offset.copy()
    
    def set_uv_scale(self, scale: List[float]):
        """Set UV scale for tiling"""
        self.uv_scale = scale.copy() if isinstance(scale, list) else list(scale)
    
    def get_uv_scale(self) -> List[float]:
        """Get UV scale"""
        return self.uv_scale.copy()
    
    def set_flip(self, horizontal: bool, vertical: bool):
        """Set texture flipping"""
        self.flip_h = horizontal
        self.flip_v = vertical
    
    def set_texture_rotation(self, degrees: float):
        """Set texture rotation in degrees"""
        self.rotation = degrees % 360.0

    def set_region(self, enabled: bool, rect: Optional[List[float]] = None):
        """Set texture region (for sprite sheets)"""
        self.use_region = enabled
        if rect:
            # Ensure region coordinates are normalized [0-1]
            self.region_rect = [
                max(0.0, min(1.0, rect[0])),  # x
                max(0.0, min(1.0, rect[1])),  # y
                max(0.0, min(1.0, rect[2])),  # width
                max(0.0, min(1.0, rect[3]))   # height
            ]
    
    def set_modulate(self, color: List[float]):
        """Set color modulation"""
        self.modulate_color = color.copy() if isinstance(color, list) else list(color)
    
    def get_modulate(self) -> List[float]:
        """Get color modulation"""
        return self.modulate_color.copy()
    
    def set_uv_animation_speed(self, speed: List[float]):
        """Set UV scrolling animation speed"""
        self.uv_animation_speed = speed.copy() if isinstance(speed, list) else list(speed)
    
    def get_effective_uv_transform(self) -> Dict[str, Any]:
        """Get the effective UV transformation parameters"""
        return {
            "offset": self.uv_offset.copy(),
            "scale": self.uv_scale.copy(),
            "flip_h": self.flip_h,
            "flip_v": self.flip_v,
            "rotation": self.rotation,
            "region": self.region_rect.copy() if self.use_region else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add TextureRect-specific properties
        data.update({
            "texture": self.texture_path,  # Export variable
            "texture_path": self.texture_path,  # Internal property
            "stretch_mode": self.stretch_mode,
            "expand": self.expand,
            "filter": self.filter,
            "uv_offset": self.uv_offset,
            "uv_scale": self.uv_scale,
            "flip_h": self.flip_h,
            "flip_v": self.flip_v,
            "rotation": self.rotation,
            "use_region": self.use_region,
            "region_rect": self.region_rect,
            "modulate_color": self.modulate_color,
            "uv_animation_speed": self.uv_animation_speed,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextureRect":
        """Create from dictionary"""
        texture_rect = cls(data.get("name", "TextureRect"))
        cls._apply_node_properties(texture_rect, data)
        
        # Apply TextureRect properties
        # Handle both 'texture' (export variable) and 'texture_path' (internal property)
        texture_path = data.get("texture_path", "") or data.get("texture", "")
        texture_rect.texture_path = texture_path
        texture_rect.texture = texture_path  # Keep export variable in sync
        texture_rect.stretch_mode = data.get("stretch_mode", "stretch")
        texture_rect.expand = data.get("expand", False)
        texture_rect.filter = data.get("filter", True)
        texture_rect.uv_offset = data.get("uv_offset", [0.0, 0.0])
        texture_rect.uv_scale = data.get("uv_scale", [1.0, 1.0])
        texture_rect.flip_h = data.get("flip_h", False)
        texture_rect.flip_v = data.get("flip_v", False)
        texture_rect.rotation = data.get("rotation", 0.0)
        texture_rect.use_region = data.get("use_region", False)
        texture_rect.region_rect = data.get("region_rect", [0.0, 0.0, 1.0, 1.0])
        texture_rect.modulate_color = data.get("modulate_color", [1.0, 1.0, 1.0, 1.0])
        texture_rect.uv_animation_speed = data.get("uv_animation_speed", [0.0, 0.0])
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            texture_rect.add_child(child)
        
        return texture_rect
    
    def __str__(self) -> str:
        """String representation of the texture rect"""
        return f"TextureRect({self.name}, rect={self.get_rect()}, texture={self.texture_path})"
