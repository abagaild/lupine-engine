"""
Sprite - 2D sprite node for displaying textures
"""

from typing import Dict, Any, List, Optional
from .node2d import Node2D


class Sprite(Node2D):
    """2D sprite node for displaying textures"""
    
    def __init__(self, name: str = "Sprite", node_type: str = "Sprite"):
        super().__init__(name, node_type)
        
        # Sprite properties
        self.texture_path: Optional[str] = None
        self.texture_size: List[int] = [64, 64]  # Default size
        self.centered: bool = True
        self.offset: List[float] = [0.0, 0.0]
        self.flip_h: bool = False
        self.flip_v: bool = False
        self.modulate: List[float] = [1.0, 1.0, 1.0, 1.0]  # RGBA
        
        # Region properties for texture atlases
        self.region_enabled: bool = False
        self.region_rect: List[float] = [0.0, 0.0, 0.0, 0.0]  # x, y, width, height
        
        # Animation properties (for simple frame-based animation)
        self.hframes: int = 1
        self.vframes: int = 1
        self.frame: int = 0
    
    def set_texture(self, texture_path: str):
        """Set the texture for this sprite"""
        self.texture_path = texture_path
        # TODO: Load texture and get actual size
        # For now, keep default size
    
    def get_texture(self) -> Optional[str]:
        """Get the texture path"""
        return self.texture_path
    
    def set_centered(self, centered: bool):
        """Set whether the sprite is centered on its position"""
        self.centered = centered
    
    def is_centered(self) -> bool:
        """Check if the sprite is centered"""
        return self.centered
    
    def set_offset(self, x: float, y: float):
        """Set the texture offset"""
        self.offset = [x, y]
    
    def get_offset(self) -> List[float]:
        """Get the texture offset"""
        return self.offset.copy()
    
    def set_flip_h(self, flip: bool):
        """Set horizontal flip"""
        self.flip_h = flip
    
    def set_flip_v(self, flip: bool):
        """Set vertical flip"""
        self.flip_v = flip
    
    def set_modulate(self, r: float, g: float, b: float, a: float = 1.0):
        """Set the modulate color (tint)"""
        self.modulate = [r, g, b, a]
    
    def get_modulate(self) -> List[float]:
        """Get the modulate color"""
        return self.modulate.copy()
    
    def set_region_rect(self, x: float, y: float, width: float, height: float):
        """Set the region rectangle for texture atlas"""
        self.region_enabled = True
        self.region_rect = [x, y, width, height]
    
    def get_region_rect(self) -> List[float]:
        """Get the region rectangle"""
        return self.region_rect.copy()
    
    def set_frame(self, frame: int):
        """Set the current frame for animation"""
        if 0 <= frame < self.hframes * self.vframes:
            self.frame = frame
    
    def get_frame(self) -> int:
        """Get the current frame"""
        return self.frame
    
    def set_hframes(self, hframes: int):
        """Set the number of horizontal frames"""
        self.hframes = max(1, hframes)
    
    def set_vframes(self, vframes: int):
        """Set the number of vertical frames"""
        self.vframes = max(1, vframes)
    
    def get_frame_coords(self) -> tuple:
        """Get the texture coordinates for the current frame"""
        if self.hframes <= 1 and self.vframes <= 1:
            return (0.0, 0.0, 1.0, 1.0)  # Full texture
        
        frame_width = 1.0 / self.hframes
        frame_height = 1.0 / self.vframes
        
        frame_x = (self.frame % self.hframes) * frame_width
        frame_y = (self.frame // self.hframes) * frame_height
        
        return (frame_x, frame_y, frame_width, frame_height)
    
    def get_rect(self) -> List[float]:
        """Get the sprite's bounding rectangle in local coordinates"""
        width = self.texture_size[0] * self.scale[0]
        height = self.texture_size[1] * self.scale[1]
        
        if self.centered:
            x = self.position[0] - width / 2 + self.offset[0]
            y = self.position[1] - height / 2 + self.offset[1]
        else:
            x = self.position[0] + self.offset[0]
            y = self.position[1] + self.offset[1]
        
        return [x, y, width, height]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "texture_path": self.texture_path,
            "texture_size": self.texture_size.copy(),
            "centered": self.centered,
            "offset": self.offset.copy(),
            "flip_h": self.flip_h,
            "flip_v": self.flip_v,
            "modulate": self.modulate.copy(),
            "region_enabled": self.region_enabled,
            "region_rect": self.region_rect.copy(),
            "hframes": self.hframes,
            "vframes": self.vframes,
            "frame": self.frame
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sprite":
        """Create from dictionary"""
        node = cls(data.get("name", "Sprite"), data.get("type", "Sprite"))
        cls._apply_node_properties(node, data)
        
        # Apply Node2D properties
        node.position = data.get("position", [0.0, 0.0])
        node.rotation = data.get("rotation", 0.0)
        node.scale = data.get("scale", [1.0, 1.0])
        node.z_index = data.get("z_index", 0)
        node.z_as_relative = data.get("z_as_relative", True)
        
        # Apply Sprite specific properties
        node.texture_path = data.get("texture_path")
        node.texture_size = data.get("texture_size", [64, 64])
        node.centered = data.get("centered", True)
        node.offset = data.get("offset", [0.0, 0.0])
        node.flip_h = data.get("flip_h", False)
        node.flip_v = data.get("flip_v", False)
        node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        node.region_enabled = data.get("region_enabled", False)
        node.region_rect = data.get("region_rect", [0.0, 0.0, 0.0, 0.0])
        node.hframes = data.get("hframes", 1)
        node.vframes = data.get("vframes", 1)
        node.frame = data.get("frame", 0)
        
        # Create children
        for child_data in data.get("children", []):
            from .base_node import Node
            child = Node.from_dict(child_data)
            node.add_child(child)
        
        return node
