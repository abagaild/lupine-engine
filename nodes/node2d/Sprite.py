"""
Sprite node implementation for Lupine Engine
2D sprite rendering with texture support
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional
import os


class Sprite(Node2D):
    """
    2D sprite node for displaying textures and images.
    
    Features:
    - Texture loading and display
    - Texture regions and frames
    - Modulation color and alpha
    - Flip horizontal/vertical
    - Centered and offset positioning
    - Texture filtering options
    - Animation frame support
    """
    
    def __init__(self, name: str = "Sprite"):
        super().__init__(name)
        self.type = "Sprite"
        
        # Export variables for editor
        self.export_variables.update({
            "texture": {
                "type": "path",
                "value": "",
                "filter": "*.png,*.jpg,*.jpeg,*.bmp,*.tga",
                "description": "Texture file to display"
            },
            "centered": {
                "type": "bool",
                "value": True,
                "description": "If true, texture is centered on the node"
            },
            "offset": {
                "type": "vector2",
                "value": [0.0, 0.0],
                "description": "Offset from the node position"
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
            "modulate": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Color modulation (RGBA)"
            },
            "region_enabled": {
                "type": "bool",
                "value": False,
                "description": "Enable texture region"
            },
            "region_rect": {
                "type": "rect2",
                "value": [0.0, 0.0, 0.0, 0.0],
                "description": "Texture region rectangle (x, y, width, height)"
            },
            "filter": {
                "type": "bool",
                "value": True,
                "description": "Enable texture filtering"
            },
            "normal_map": {
                "type": "path",
                "value": "",
                "filter": "*.png,*.jpg,*.jpeg,*.bmp,*.tga",
                "description": "Normal map texture file"
            }
        })
        
        # Sprite properties
        self.texture: str = ""
        self.centered: bool = True
        self.offset: List[float] = [0.0, 0.0]
        self.flip_h: bool = False
        self.flip_v: bool = False
        self.modulate: List[float] = [1.0, 1.0, 1.0, 1.0]  # RGBA
        self.region_enabled: bool = False
        self.region_rect: List[float] = [0.0, 0.0, 0.0, 0.0]  # x, y, width, height
        
        # Texture properties (loaded at runtime)
        self._texture_size: List[int] = [0, 0]
        self._texture_loaded: bool = False
        self._texture_path: str = ""
        
        # Rendering properties
        self.filter: bool = True
        self.normal_map: str = ""
        
        # Built-in signals
        self.add_signal("texture_changed")
        self.add_signal("frame_changed")
    
    def set_texture(self, texture_path: str):
        """Set the texture file path"""
        old_texture = self.texture
        self.texture = texture_path
        
        if old_texture != texture_path:
            self._load_texture()
            self.emit_signal("texture_changed", old_texture, texture_path)
    
    def get_texture(self) -> str:
        """Get the texture file path"""
        return self.texture
    
    def _load_texture(self):
        """Load texture information (size, etc.)"""
        if not self.texture or not os.path.exists(self.texture):
            self._texture_loaded = False
            self._texture_size = [0, 0]
            return
        
        try:
            # In a full implementation, this would load the actual texture
            # For now, we'll simulate texture loading
            self._texture_path = self.texture
            self._texture_loaded = True
            
            # Simulate getting texture size (would use actual image library)
            # Default to common sizes for testing
            if "icon" in self.texture.lower():
                self._texture_size = [64, 64]
            elif "sprite" in self.texture.lower():
                self._texture_size = [32, 32]
            else:
                self._texture_size = [128, 128]
                
        except Exception as e:
            print(f"Error loading texture {self.texture}: {e}")
            self._texture_loaded = False
            self._texture_size = [0, 0]
    
    def get_texture_size(self) -> List[int]:
        """Get the size of the loaded texture"""
        return self._texture_size.copy()
    
    def is_texture_loaded(self) -> bool:
        """Check if texture is loaded"""
        return self._texture_loaded
    
    def set_centered(self, centered: bool):
        """Set whether the sprite is centered"""
        self.centered = centered
    
    def is_centered(self) -> bool:
        """Check if the sprite is centered"""
        return self.centered
    
    def set_offset(self, x: float, y: float):
        """Set the sprite offset"""
        self.offset = [x, y]
    
    def get_offset(self) -> List[float]:
        """Get the sprite offset"""
        return self.offset.copy()
    
    def set_flip_h(self, flip: bool):
        """Set horizontal flip"""
        self.flip_h = flip
    
    def is_flipped_h(self) -> bool:
        """Check if horizontally flipped"""
        return self.flip_h
    
    def set_flip_v(self, flip: bool):
        """Set vertical flip"""
        self.flip_v = flip
    
    def is_flipped_v(self) -> bool:
        """Check if vertically flipped"""
        return self.flip_v
    
    def set_modulate(self, r: float, g: float, b: float, a: float = 1.0):
        """Set the modulation color"""
        self.modulate = [r, g, b, a]
    
    def get_modulate(self) -> List[float]:
        """Get the modulation color"""
        return self.modulate.copy()
    
    def set_region_enabled(self, enabled: bool):
        """Enable or disable texture region"""
        self.region_enabled = enabled
    
    def is_region_enabled(self) -> bool:
        """Check if texture region is enabled"""
        return self.region_enabled
    
    def set_region_rect(self, x: float, y: float, width: float, height: float):
        """Set the texture region rectangle"""
        self.region_rect = [x, y, width, height]
    
    def get_region_rect(self) -> List[float]:
        """Get the texture region rectangle"""
        return self.region_rect.copy()
    
    def get_rect(self) -> List[float]:
        """Get the sprite's bounding rectangle"""
        if not self._texture_loaded:
            return [0.0, 0.0, 0.0, 0.0]
        
        width = self._texture_size[0]
        height = self._texture_size[1]
        
        # Use region size if enabled
        if self.region_enabled and self.region_rect[2] > 0 and self.region_rect[3] > 0:
            width = self.region_rect[2]
            height = self.region_rect[3]
        
        # Apply scale
        width *= abs(self.scale[0])
        height *= abs(self.scale[1])
        
        # Calculate position based on centering
        x = self.position[0] + self.offset[0]
        y = self.position[1] + self.offset[1]
        
        if self.centered:
            x -= width / 2
            y -= height / 2
        
        return [x, y, width, height]
    
    def get_global_rect(self) -> List[float]:
        """Get the sprite's global bounding rectangle"""
        local_rect = self.get_rect()
        global_pos = self.get_global_position()
        
        # Transform the rectangle to global coordinates
        # This is a simplified version - full implementation would handle rotation
        return [
            global_pos[0] + local_rect[0] - self.position[0],
            global_pos[1] + local_rect[1] - self.position[1],
            local_rect[2],
            local_rect[3]
        ]
    
    def is_pixel_opaque(self, x: float, y: float) -> bool:
        """Check if a pixel at local coordinates is opaque"""
        # This would require actual texture data in a full implementation
        rect = self.get_rect()
        return (rect[0] <= x <= rect[0] + rect[2] and 
                rect[1] <= y <= rect[1] + rect[3])
    
    def set_normal_map(self, normal_map_path: str):
        """Set the normal map texture"""
        self.normal_map = normal_map_path
    
    def get_normal_map(self) -> str:
        """Get the normal map texture path"""
        return self.normal_map
    
    def set_filter(self, filter_enabled: bool):
        """Set texture filtering"""
        self.filter = filter_enabled
    
    def is_filter_enabled(self) -> bool:
        """Check if texture filtering is enabled"""
        return self.filter
    
    def duplicate_sprite(self) -> "Sprite":
        """Create a duplicate of this sprite"""
        duplicate = Sprite(f"{self.name}_copy")
        
        # Copy all properties
        duplicate.texture = self.texture
        duplicate.centered = self.centered
        duplicate.offset = self.offset.copy()
        duplicate.flip_h = self.flip_h
        duplicate.flip_v = self.flip_v
        duplicate.modulate = self.modulate.copy()
        duplicate.region_enabled = self.region_enabled
        duplicate.region_rect = self.region_rect.copy()
        duplicate.filter = self.filter
        duplicate.normal_map = self.normal_map
        
        # Copy transform
        duplicate.position = self.position.copy()
        duplicate.rotation = self.rotation
        duplicate.scale = self.scale.copy()
        duplicate.z_index = self.z_index
        
        return duplicate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "texture": self.texture,
            "centered": self.centered,
            "offset": self.offset.copy(),
            "flip_h": self.flip_h,
            "flip_v": self.flip_v,
            "modulate": self.modulate.copy(),
            "region_enabled": self.region_enabled,
            "region_rect": self.region_rect.copy(),
            "filter": self.filter,
            "normal_map": self.normal_map
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sprite":
        """Create from dictionary"""
        sprite = cls(data.get("name", "Sprite"))
        cls._apply_node_properties(sprite, data)
        
        # Apply Node2D properties
        sprite.position = data.get("position", [0.0, 0.0])
        sprite.rotation = data.get("rotation", 0.0)
        sprite.scale = data.get("scale", [1.0, 1.0])
        sprite.z_index = data.get("z_index", 0)
        sprite.z_as_relative = data.get("z_as_relative", True)
        
        # Apply Sprite specific properties
        sprite.texture = data.get("texture", "")
        sprite.centered = data.get("centered", True)
        sprite.offset = data.get("offset", [0.0, 0.0])
        sprite.flip_h = data.get("flip_h", False)
        sprite.flip_v = data.get("flip_v", False)
        sprite.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        sprite.region_enabled = data.get("region_enabled", False)
        sprite.region_rect = data.get("region_rect", [0.0, 0.0, 0.0, 0.0])
        sprite.filter = data.get("filter", True)
        sprite.normal_map = data.get("normal_map", "")
        
        # Load texture if specified
        if sprite.texture:
            sprite._load_texture()
        
        # Create children using proper node loading
        for child_data in data.get("children", []):
            try:
                # Try to use the scene manager's node creation method
                from core.scene.scene_manager import Scene
                child = Scene._create_node_from_dict(child_data)
                sprite.add_child(child)
            except ImportError:
                # Fallback to base Node
                from nodes.base.Node import Node
                child = Node.from_dict(child_data)
                sprite.add_child(child)
        
        return sprite

    def __str__(self) -> str:
        """String representation of the sprite"""
        return f"Sprite({self.name}, texture={self.texture}, size={self._texture_size})"
