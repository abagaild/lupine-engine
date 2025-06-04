"""
NinePatchRect node implementation for Lupine Engine
9-patch scalable UI panel with texture atlas support
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class NinePatchRect(Control):
    """
    9-patch scalable UI panel with texture atlas support.
    
    Features:
    - 9-patch texture scaling (corners, edges, center)
    - Customizable patch margins
    - Texture atlas support
    - Draw center option
    - Axis stretch modes
    - Modulation and filtering
    - Region-based 9-patch definition
    """
    
    def __init__(self, name: str = "NinePatchRect"):
        super().__init__(name)
        self.type = "NinePatchRect"
        
        # Texture properties
        self.texture_path = None
        self.texture = None  # Will hold the actual texture object
        
        # 9-patch margins (in pixels from texture edges)
        self.patch_margin_left = 0
        self.patch_margin_top = 0
        self.patch_margin_right = 0
        self.patch_margin_bottom = 0
        
        # Draw options
        self.draw_center = True  # Whether to draw the center patch
        
        # Axis stretch modes
        self.axis_stretch_horizontal = "stretch"  # stretch, tile, tile_fit
        self.axis_stretch_vertical = "stretch"    # stretch, tile, tile_fit
        
        # Texture region (for texture atlases)
        self.use_region = False
        self.region_rect = [0.0, 0.0, 1.0, 1.0]  # Normalized coordinates [x, y, width, height]
        
        # Visual properties
        self.modulate_color = [1.0, 1.0, 1.0, 1.0]  # RGBA multiplier
        self.filter = True  # Linear filtering
        
        # Advanced options
        self.patch_scale = 1.0  # Scale factor for patch margins
        
        # Built-in signals
        self.add_signal("texture_changed")
        self.add_signal("patch_margins_changed")
    
    def set_texture(self, texture_path: str):
        """Set the texture from a file path"""
        old_path = self.texture_path
        self.texture_path = texture_path
        
        if old_path != texture_path:
            self.emit_signal("texture_changed", texture_path)
    
    def get_texture_path(self) -> Optional[str]:
        """Get the texture file path"""
        return self.texture_path
    
    def set_patch_margin(self, left: int, top: int, right: int, bottom: int):
        """Set all patch margins in pixels"""
        old_margins = [self.patch_margin_left, self.patch_margin_top, 
                      self.patch_margin_right, self.patch_margin_bottom]
        
        self.patch_margin_left = max(0, left)
        self.patch_margin_top = max(0, top)
        self.patch_margin_right = max(0, right)
        self.patch_margin_bottom = max(0, bottom)
        
        new_margins = [self.patch_margin_left, self.patch_margin_top, 
                      self.patch_margin_right, self.patch_margin_bottom]
        
        if old_margins != new_margins:
            self.emit_signal("patch_margins_changed", new_margins)
    
    def set_patch_margin_left(self, margin: int):
        """Set left patch margin"""
        self.patch_margin_left = max(0, margin)
        self.emit_signal("patch_margins_changed", self.get_patch_margins())
    
    def set_patch_margin_top(self, margin: int):
        """Set top patch margin"""
        self.patch_margin_top = max(0, margin)
        self.emit_signal("patch_margins_changed", self.get_patch_margins())
    
    def set_patch_margin_right(self, margin: int):
        """Set right patch margin"""
        self.patch_margin_right = max(0, margin)
        self.emit_signal("patch_margins_changed", self.get_patch_margins())
    
    def set_patch_margin_bottom(self, margin: int):
        """Set bottom patch margin"""
        self.patch_margin_bottom = max(0, margin)
        self.emit_signal("patch_margins_changed", self.get_patch_margins())
    
    def get_patch_margins(self) -> List[int]:
        """Get patch margins as [left, top, right, bottom]"""
        return [self.patch_margin_left, self.patch_margin_top, 
                self.patch_margin_right, self.patch_margin_bottom]
    
    def set_draw_center(self, draw: bool):
        """Set whether to draw the center patch"""
        self.draw_center = draw
    
    def get_draw_center(self) -> bool:
        """Get whether center patch is drawn"""
        return self.draw_center
    
    def set_h_axis_stretch_mode(self, mode: str):
        """Set horizontal axis stretch mode"""
        valid_modes = ["stretch", "tile", "tile_fit"]
        if mode in valid_modes:
            self.axis_stretch_horizontal = mode
        else:
            print(f"Warning: Invalid horizontal stretch mode '{mode}'. Valid modes: {valid_modes}")
    
    def set_v_axis_stretch_mode(self, mode: str):
        """Set vertical axis stretch mode"""
        valid_modes = ["stretch", "tile", "tile_fit"]
        if mode in valid_modes:
            self.axis_stretch_vertical = mode
        else:
            print(f"Warning: Invalid vertical stretch mode '{mode}'. Valid modes: {valid_modes}")
    
    def set_region(self, enabled: bool, rect: List[float] = None):
        """Set texture region for atlas support"""
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
    
    def set_filter(self, filter_enabled: bool):
        """Set texture filtering"""
        self.filter = filter_enabled
    
    def set_patch_scale(self, scale: float):
        """Set patch scale factor"""
        self.patch_scale = max(0.1, scale)
    
    def get_effective_patch_margins(self) -> List[float]:
        """Get effective patch margins considering scale"""
        return [
            self.patch_margin_left * self.patch_scale,
            self.patch_margin_top * self.patch_scale,
            self.patch_margin_right * self.patch_scale,
            self.patch_margin_bottom * self.patch_scale
        ]
    
    def get_nine_patch_rects(self) -> Dict[str, List[float]]:
        """Get the 9 patch rectangles for rendering"""
        # This calculates the 9 rectangles needed for 9-patch rendering
        # Returns normalized UV coordinates for each patch
        
        if not self.use_region:
            # Use full texture
            tex_left, tex_top = 0.0, 0.0
            tex_width, tex_height = 1.0, 1.0
        else:
            # Use specified region
            tex_left, tex_top = self.region_rect[0], self.region_rect[1]
            tex_width, tex_height = self.region_rect[2], self.region_rect[3]
        
        # Calculate patch boundaries in normalized coordinates
        # This is a simplified version - actual implementation would need texture dimensions
        margin_left_norm = self.patch_margin_left / 100.0  # Placeholder normalization
        margin_top_norm = self.patch_margin_top / 100.0
        margin_right_norm = self.patch_margin_right / 100.0
        margin_bottom_norm = self.patch_margin_bottom / 100.0
        
        return {
            "top_left": [tex_left, tex_top, margin_left_norm, margin_top_norm],
            "top_center": [tex_left + margin_left_norm, tex_top, 
                          tex_width - margin_left_norm - margin_right_norm, margin_top_norm],
            "top_right": [tex_left + tex_width - margin_right_norm, tex_top, 
                         margin_right_norm, margin_top_norm],
            "middle_left": [tex_left, tex_top + margin_top_norm, 
                           margin_left_norm, tex_height - margin_top_norm - margin_bottom_norm],
            "middle_center": [tex_left + margin_left_norm, tex_top + margin_top_norm,
                             tex_width - margin_left_norm - margin_right_norm,
                             tex_height - margin_top_norm - margin_bottom_norm],
            "middle_right": [tex_left + tex_width - margin_right_norm, tex_top + margin_top_norm,
                            margin_right_norm, tex_height - margin_top_norm - margin_bottom_norm],
            "bottom_left": [tex_left, tex_top + tex_height - margin_bottom_norm,
                           margin_left_norm, margin_bottom_norm],
            "bottom_center": [tex_left + margin_left_norm, tex_top + tex_height - margin_bottom_norm,
                             tex_width - margin_left_norm - margin_right_norm, margin_bottom_norm],
            "bottom_right": [tex_left + tex_width - margin_right_norm, 
                            tex_top + tex_height - margin_bottom_norm,
                            margin_right_norm, margin_bottom_norm]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add NinePatchRect-specific properties
        data.update({
            "texture_path": self.texture_path,
            "patch_margin_left": self.patch_margin_left,
            "patch_margin_top": self.patch_margin_top,
            "patch_margin_right": self.patch_margin_right,
            "patch_margin_bottom": self.patch_margin_bottom,
            "draw_center": self.draw_center,
            "axis_stretch_horizontal": self.axis_stretch_horizontal,
            "axis_stretch_vertical": self.axis_stretch_vertical,
            "use_region": self.use_region,
            "region_rect": self.region_rect,
            "modulate_color": self.modulate_color,
            "filter": self.filter,
            "patch_scale": self.patch_scale,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NinePatchRect":
        """Create from dictionary"""
        nine_patch = cls(data.get("name", "NinePatchRect"))
        cls._apply_node_properties(nine_patch, data)
        
        # Apply NinePatchRect properties
        nine_patch.texture_path = data.get("texture_path", None)
        nine_patch.patch_margin_left = data.get("patch_margin_left", 0)
        nine_patch.patch_margin_top = data.get("patch_margin_top", 0)
        nine_patch.patch_margin_right = data.get("patch_margin_right", 0)
        nine_patch.patch_margin_bottom = data.get("patch_margin_bottom", 0)
        nine_patch.draw_center = data.get("draw_center", True)
        nine_patch.axis_stretch_horizontal = data.get("axis_stretch_horizontal", "stretch")
        nine_patch.axis_stretch_vertical = data.get("axis_stretch_vertical", "stretch")
        nine_patch.use_region = data.get("use_region", False)
        nine_patch.region_rect = data.get("region_rect", [0.0, 0.0, 1.0, 1.0])
        nine_patch.modulate_color = data.get("modulate_color", [1.0, 1.0, 1.0, 1.0])
        nine_patch.filter = data.get("filter", True)
        nine_patch.patch_scale = data.get("patch_scale", 1.0)
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            nine_patch.add_child(child)
        
        return nine_patch
    
    def __str__(self) -> str:
        """String representation of the nine patch rect"""
        return f"NinePatchRect({self.name}, rect={self.get_rect()}, texture={self.texture_path})"
