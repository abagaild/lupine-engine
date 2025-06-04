"""
TileMap node implementation for Lupine Engine
Grid of tiles with tileset, collision layers, and batch rendering
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class TileMap(Node2D):
    """
    TileMap for painting tiles on a grid.
    
    Features:
    - Tileset reference
    - Cell size and origin
    - Per-cell tile index storage
    - Collision layer/mask
    - Modulate and opacity
    """

    def __init__(self, name: str = "TileMap"):
        super().__init__(name)
        self.type = "TileMap"

        # Export variables for editor
        self.export_variables = {
            "tileset": {
                "type": "path",
                "value": "",
                "filter": "*.tres,*.json",
                "description": "Path to TileSet resource"
            },
            "cell_size": {
                "type": "vector2",
                "value": [32.0, 32.0],
                "description": "Width/height of a single tile"
            },
            "cell_origin": {
                "type": "enum",
                "value": "TopLeft",
                "options": ["TopLeft", "Center"],
                "description": "Origin point of the grid"
            },
            "mode": {
                "type": "enum",
                "value": "Square",
                "options": ["Square", "Hexagonal", "Isometric"],
                "description": "Tilemap drawing mode"
            },
            "modulate": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Color modulation for the entire TileMap"
            },
            "opacity": {
                "type": "float",
                "value": 1.0,
                "min": 0.0,
                "max": 1.0,
                "description": "Opacity for the entire TileMap"
            },
            "collision_layer": {
                "type": "int",
                "value": 1,
                "description": "Physics layer this TileMap occupies"
            },
            "collision_mask": {
                "type": "int",
                "value": 1,
                "description": "Which layers this TileMap collides with"
            },
            "one_way_collision_enabled": {
                "type": "bool",
                "value": False,
                "description": "Enable one-way collisions (like platforms)"
            },
            "one_way_collision_margin": {
                "type": "float",
                "value": 0.0,
                "description": "Margin for one-way collision"
            }
        }

        # Core properties
        self.tileset: str = ""
        self.cell_size: List[float] = [32.0, 32.0]
        self.cell_origin: str = "TopLeft"
        self.mode: str = "Square"
        self.modulate: List[float] = [1.0, 1.0, 1.0, 1.0]
        self.opacity: float = 1.0
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self.one_way_collision_enabled: bool = False
        self.one_way_collision_margin: float = 0.0

        # Internal tile data: mapping (x, y) → tile index (int)
        self._tiles: Dict[str, int] = {}  # e.g. {"0,0": 5, "1,0": 2}

        # Built-in signals
        self.add_signal("tiles_changed")

    # Tile editing API
    def set_tile(self, x: int, y: int, tile_index: int):
        """Assign a tile index at grid cell (x, y)."""
        key = f"{x},{y}"
        old = self._tiles.get(key, -1)
        if tile_index < 0:
            if key in self._tiles:
                del self._tiles[key]
        else:
            self._tiles[key] = tile_index
        if old != tile_index:
            self.emit_signal("tiles_changed", x, y, old, tile_index)

    def get_tile(self, x: int, y: int) -> int:
        """Retrieve the tile index at (x, y), or -1 if none."""
        return self._tiles.get(f"{x},{y}", -1)

    def clear_tile(self, x: int, y: int):
        """Remove any tile at (x, y)."""
        self.set_tile(x, y, -1)

    def clear_all(self):
        """Remove all tiles from the map."""
        self._tiles.clear()
        self.emit_signal("tiles_changed", None, None, None, None)

    # Utility methods for tile manipulation
    def get_used_cells(self) -> List[List[int]]:
        """Get a list of all cells that have tiles"""
        cells = []
        for key in self._tiles.keys():
            x, y = map(int, key.split(','))
            cells.append([x, y])
        return cells

    def get_used_rect(self) -> List[int]:
        """Get the rectangle that encompasses all used tiles"""
        if not self._tiles:
            return [0, 0, 0, 0]

        cells = self.get_used_cells()
        min_x = min(cell[0] for cell in cells)
        max_x = max(cell[0] for cell in cells)
        min_y = min(cell[1] for cell in cells)
        max_y = max(cell[1] for cell in cells)

        return [min_x, min_y, max_x - min_x + 1, max_y - min_y + 1]

    def world_to_map(self, world_pos: List[float]) -> List[int]:
        """Convert world position to map coordinates"""
        # Adjust for node position
        local_x = world_pos[0] - self.position[0]
        local_y = world_pos[1] - self.position[1]

        # Convert to tile coordinates
        tile_x = int(local_x // self.cell_size[0])
        tile_y = int(local_y // self.cell_size[1])

        return [tile_x, tile_y]

    def map_to_world(self, map_pos: List[int]) -> List[float]:
        """Convert map coordinates to world position"""
        # Calculate world position based on cell origin
        if self.cell_origin == "Center":
            world_x = map_pos[0] * self.cell_size[0] + self.cell_size[0] / 2
            world_y = map_pos[1] * self.cell_size[1] + self.cell_size[1] / 2
        else:  # TopLeft
            world_x = map_pos[0] * self.cell_size[0]
            world_y = map_pos[1] * self.cell_size[1]

        # Adjust for node position
        world_x += self.position[0]
        world_y += self.position[1]

        return [world_x, world_y]

    def get_cell_rect(self, x: int, y: int) -> List[float]:
        """Get the world rectangle for a specific cell"""
        world_pos = self.map_to_world([x, y])

        if self.cell_origin == "Center":
            rect_x = world_pos[0] - self.cell_size[0] / 2
            rect_y = world_pos[1] - self.cell_size[1] / 2
        else:  # TopLeft
            rect_x = world_pos[0]
            rect_y = world_pos[1]

        return [rect_x, rect_y, self.cell_size[0], self.cell_size[1]]

    def set_tileset(self, tileset_path: str):
        """Set the tileset resource path"""
        self.tileset = tileset_path

    def get_tileset(self) -> str:
        """Get the tileset resource path"""
        return self.tileset

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TileMap to a dictionary."""
        data = super().to_dict()
        data.update({
            "tileset": self.tileset,
            "cell_size": self.cell_size.copy(),
            "cell_origin": self.cell_origin,
            "mode": self.mode,
            "modulate": self.modulate.copy(),
            "opacity": self.opacity,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "one_way_collision_enabled": self.one_way_collision_enabled,
            "one_way_collision_margin": self.one_way_collision_margin,
            "tiles": self._tiles.copy()
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TileMap":
        """Deserialize a TileMap from a dictionary."""
        tilemap = cls(data.get("name", "TileMap"))
        cls._apply_node_properties(tilemap, data)

        tilemap.tileset = data.get("tileset", "")
        tilemap.cell_size = data.get("cell_size", [32.0, 32.0])
        tilemap.cell_origin = data.get("cell_origin", "TopLeft")
        tilemap.mode = data.get("mode", "Square")
        tilemap.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        tilemap.opacity = data.get("opacity", 1.0)
        tilemap.collision_layer = data.get("collision_layer", 1)
        tilemap.collision_mask = data.get("collision_mask", 1)
        tilemap.one_way_collision_enabled = data.get("one_way_collision_enabled", False)
        tilemap.one_way_collision_margin = data.get("one_way_collision_margin", 0.0)
        tilemap._tiles = data.get("tiles", {}).copy()

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            tilemap.add_child(child)
        return tilemap
