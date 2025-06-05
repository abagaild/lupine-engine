"""
TileSet resource for Lupine Engine
Manages tile definitions, collision shapes, tags, and texture atlases
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class TileDefinition:
    """Individual tile definition within a tileset"""
    
    def __init__(self, tile_id: int):
        self.tile_id = tile_id
        self.name = f"Tile_{tile_id}"
        self.texture_rect = [0, 0, 32, 32]  # x, y, width, height in texture
        self.collision_shapes = []  # List of collision shape definitions
        self.tags = []  # List of string tags
        self.custom_properties = {}  # Custom user-defined properties
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "tile_id": self.tile_id,
            "name": self.name,
            "texture_rect": self.texture_rect.copy(),
            "collision_shapes": [shape.copy() for shape in self.collision_shapes],
            "tags": self.tags.copy(),
            "custom_properties": self.custom_properties.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TileDefinition":
        """Create from dictionary"""
        tile = cls(data.get("tile_id", 0))
        tile.name = data.get("name", f"Tile_{tile.tile_id}")
        tile.texture_rect = data.get("texture_rect", [0, 0, 32, 32])
        tile.collision_shapes = data.get("collision_shapes", [])
        tile.tags = data.get("tags", [])
        tile.custom_properties = data.get("custom_properties", {})
        return tile


class TileSet:
    """TileSet resource containing multiple tile definitions"""
    
    def __init__(self, name: str = "New TileSet"):
        self.name = name
        self.texture_path = ""  # Path to the texture atlas
        self.tile_size = [32, 32]  # Default tile size
        self.margin = [0, 0]  # Margin around tiles in texture
        self.spacing = [0, 0]  # Spacing between tiles in texture
        self.tiles = {}  # Dict[int, TileDefinition]
        self.next_tile_id = 0
        
        # Metadata
        self.description = ""
        self.version = "1.0"
        
    def add_tile(self, tile_def: Optional[TileDefinition] = None) -> TileDefinition:
        """Add a new tile definition"""
        if tile_def is None:
            tile_def = TileDefinition(self.next_tile_id)
        
        self.tiles[tile_def.tile_id] = tile_def
        self.next_tile_id = max(self.next_tile_id + 1, tile_def.tile_id + 1)
        return tile_def
    
    def remove_tile(self, tile_id: int) -> bool:
        """Remove a tile definition"""
        if tile_id in self.tiles:
            del self.tiles[tile_id]
            return True
        return False
    
    def get_tile(self, tile_id: int) -> Optional[TileDefinition]:
        """Get a tile definition by ID"""
        return self.tiles.get(tile_id)
    
    def get_tiles_with_tag(self, tag: str) -> List[TileDefinition]:
        """Get all tiles that have a specific tag"""
        return [tile for tile in self.tiles.values() if tag in tile.tags]
    
    def auto_generate_tiles_from_texture(self, texture_width: int, texture_height: int):
        """Auto-generate tile definitions based on texture size and tile size"""
        self.tiles.clear()
        self.next_tile_id = 0
        
        tile_w, tile_h = self.tile_size
        margin_x, margin_y = self.margin
        spacing_x, spacing_y = self.spacing
        
        # Calculate how many tiles fit in the texture
        available_width = texture_width - 2 * margin_x
        available_height = texture_height - 2 * margin_y
        
        tiles_x = (available_width + spacing_x) // (tile_w + spacing_x)
        tiles_y = (available_height + spacing_y) // (tile_h + spacing_y)
        
        tile_id = 0
        for y in range(tiles_y):
            for x in range(tiles_x):
                # Calculate texture rect for this tile
                rect_x = margin_x + x * (tile_w + spacing_x)
                rect_y = margin_y + y * (tile_h + spacing_y)
                
                tile_def = TileDefinition(tile_id)
                tile_def.texture_rect = [rect_x, rect_y, tile_w, tile_h]
                tile_def.name = f"Tile_{x}_{y}"
                
                self.add_tile(tile_def)
                tile_id += 1
    
    def get_tile_at_position(self, x: int, y: int) -> Optional[TileDefinition]:
        """Get tile at grid position (for texture atlas)"""
        tile_w, tile_h = self.tile_size
        margin_x, margin_y = self.margin
        spacing_x, spacing_y = self.spacing
        
        # Calculate tile ID based on position
        tiles_per_row = self._get_tiles_per_row()
        if tiles_per_row <= 0:
            return None
            
        tile_id = y * tiles_per_row + x
        return self.get_tile(tile_id)
    
    def _get_tiles_per_row(self) -> int:
        """Calculate how many tiles fit per row in the texture"""
        if not self.texture_path:
            return 0
            
        # This would need actual texture loading to get dimensions
        # For now, assume a reasonable default
        return 16
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "texture_path": self.texture_path,
            "tile_size": self.tile_size.copy(),
            "margin": self.margin.copy(),
            "spacing": self.spacing.copy(),
            "tiles": {str(tile_id): tile.to_dict() for tile_id, tile in self.tiles.items()},
            "next_tile_id": self.next_tile_id,
            "description": self.description,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TileSet":
        """Create from dictionary"""
        tileset = cls(data.get("name", "New TileSet"))
        tileset.texture_path = data.get("texture_path", "")
        tileset.tile_size = data.get("tile_size", [32, 32])
        tileset.margin = data.get("margin", [0, 0])
        tileset.spacing = data.get("spacing", [0, 0])
        tileset.next_tile_id = data.get("next_tile_id", 0)
        tileset.description = data.get("description", "")
        tileset.version = data.get("version", "1.0")
        
        # Load tiles
        tiles_data = data.get("tiles", {})
        for tile_id_str, tile_data in tiles_data.items():
            tile_id = int(tile_id_str)
            tile_def = TileDefinition.from_dict(tile_data)
            tileset.tiles[tile_id] = tile_def
        
        return tileset
    
    def save_to_file(self, file_path: str):
        """Save tileset to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "TileSet":
        """Load tileset from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class TileSetManager:
    """Manager for loading and caching tilesets"""
    
    def __init__(self):
        self._cache = {}  # Dict[str, TileSet]
    
    def load_tileset(self, file_path: str) -> Optional[TileSet]:
        """Load a tileset, using cache if available"""
        if file_path in self._cache:
            return self._cache[file_path]
        
        try:
            if Path(file_path).exists():
                tileset = TileSet.load_from_file(file_path)
                self._cache[file_path] = tileset
                return tileset
        except Exception as e:
            print(f"Error loading tileset {file_path}: {e}")
        
        return None
    
    def clear_cache(self):
        """Clear the tileset cache"""
        self._cache.clear()
    
    def reload_tileset(self, file_path: str) -> Optional[TileSet]:
        """Force reload a tileset from disk"""
        if file_path in self._cache:
            del self._cache[file_path]
        return self.load_tileset(file_path)


# Global tileset manager instance
_tileset_manager = TileSetManager()

def get_tileset_manager() -> TileSetManager:
    """Get the global tileset manager"""
    return _tileset_manager
